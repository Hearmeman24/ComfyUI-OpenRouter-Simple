from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp

from .cancellation import NodeDeadline, NodeTimeoutError
from .http import ResponseTooLarge, read_bounded
from .models import api_base_url

MAX_ERROR_BYTES = 16_384


class OpenRouterRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatResult:
    text: str
    response_id: str | None
    usage: dict[str, Any]


def resolve_generation_key() -> str:
    return (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LLM_KEY") or "").strip()


def sanitize_message(message: str) -> str:
    message = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", message)
    message = re.sub(r"sk-or-v1-[A-Za-z0-9]+", "[REDACTED]", message)
    words: list[str] = []
    for word in message.split():
        if "://" in word:
            try:
                parts = urlsplit(word.strip("'\"(),"))
                if parts.scheme and parts.netloc:
                    word = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
            except ValueError:
                pass
        words.append(word)
    return " ".join(words)[:2000]


def _friendly_status(status: int) -> str:
    return {
        400: "OpenRouter rejected the request as invalid",
        401: "OpenRouter authentication failed; check OPENROUTER_API_KEY",
        402: "OpenRouter reported insufficient credits",
        403: "OpenRouter denied this model or request",
        408: "OpenRouter timed out while processing the request",
        413: "OpenRouter rejected the request because its encoded payload is too large",
        422: "OpenRouter could not process one of the supplied inputs",
        429: "OpenRouter rate-limited the request",
        524: "The upstream OpenRouter provider timed out",
        529: "The selected OpenRouter provider is overloaded",
    }.get(status, "OpenRouter request failed")


async def _limited_json(response: aiohttp.ClientResponse, limit: int) -> Any:
    try:
        body = await read_bounded(response.content, limit, label="OpenRouter response")
    except ResponseTooLarge as exc:
        raise OpenRouterRequestError(str(exc)) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OpenRouterRequestError("OpenRouter returned malformed JSON") from exc


def _error_detail(payload: Any) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return sanitize_message(str(error.get("message") or error.get("code") or ""))
        if error:
            return sanitize_message(str(error))
    return ""


def _extract_text(message: Any) -> str:
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"} and isinstance(block.get("text"), str):
                chunks.append(block["text"])
        return "".join(chunks)
    return ""


async def create_chat(deadline: NodeDeadline, payload: dict[str, Any], api_key: str) -> ChatResult:
    async def request() -> ChatResult:
        timeout = aiohttp.ClientTimeout(total=max(0.1, deadline.remaining))
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{api_base_url()}/chat/completions", headers=headers, json=payload) as response:
                if response.status >= 400:
                    try:
                        body = await read_bounded(response.content, MAX_ERROR_BYTES, label="OpenRouter error response")
                    except ResponseTooLarge:
                        detail = "response body omitted"
                    else:
                        try:
                            detail = _error_detail(json.loads(body))
                        except json.JSONDecodeError:
                            detail = sanitize_message(body.decode("utf-8", errors="replace"))
                    base = _friendly_status(response.status)
                    raise OpenRouterRequestError(f"{base} (HTTP {response.status})" + (f": {detail}" if detail else ""))
                data = await _limited_json(response, 2_000_000)
        choices = data.get("choices") if isinstance(data, dict) else None
        message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
        text = _extract_text(message)
        if not text:
            raise OpenRouterRequestError("OpenRouter returned no text completion; media-only output is not accepted")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return ChatResult(text=text, response_id=data.get("id"), usage=usage)

    try:
        return await deadline.run(request())
    except asyncio.TimeoutError as exc:
        raise NodeTimeoutError("OpenRouter node deadline expired") from exc


async def lookup_credits(deadline: NodeDeadline, generation_key: str) -> str:
    management_key = (os.environ.get("OPENROUTER_MANAGEMENT_KEY") or "").strip()
    key = management_key or generation_key
    endpoint = "/credits" if management_key else "/key"

    async def request() -> str:
        timeout = aiohttp.ClientTimeout(total=max(0.1, deadline.remaining))
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{api_base_url()}{endpoint}", headers={"Authorization": f"Bearer {key}"}) as response:
                if response.status >= 400:
                    raise OpenRouterRequestError(f"credits lookup returned HTTP {response.status}")
                payload = await _limited_json(response, 64_000)
        data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else {}
        if management_key:
            total = data.get("total_credits")
            used = data.get("total_usage")
            if isinstance(total, (int, float)) and isinstance(used, (int, float)):
                return f"Account credits remaining: ${max(0.0, total - used):.6f}"
            raise OpenRouterRequestError("credits response omitted total_credits or total_usage")
        remaining = data.get("limit_remaining")
        if isinstance(remaining, (int, float)):
            return f"API key limit remaining: ${remaining:.6f}"
        return "API key limit remaining: unlimited or not configured"

    try:
        return await deadline.run(request())
    except Exception as exc:
        return f"Credits unavailable ({sanitize_message(str(exc))})"
