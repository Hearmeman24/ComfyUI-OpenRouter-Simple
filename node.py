from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

from .openrouter_simple.cancellation import NodeDeadline, NodeTimeoutError
from .openrouter_simple.client import create_chat, lookup_credits, resolve_generation_key
from .openrouter_simple.media import PreparedMedia, prepare_audio, prepare_image, prepare_video
from .openrouter_simple.models import CATALOG
from .openrouter_simple.payload import build_payload

CHOOSE_MODEL = "— choose a compatible OpenRouter model —"
NO_MODEL = "— no compatible text-output model —"
MODEL_SENTINELS = {CHOOSE_MODEL, NO_MODEL, "Loading OpenRouter models…"}


async def _prepare_media(
    deadline: NodeDeadline,
    *,
    image: Any | None,
    video: Any | None,
    audio: dict[str, Any] | None,
) -> list[PreparedMedia]:
    tasks: list[asyncio.Task[PreparedMedia]] = []
    if image is not None:
        tasks.append(asyncio.create_task(prepare_image(deadline, image), name="openrouter-image"))
    if video is not None:
        tasks.append(asyncio.create_task(prepare_video(deadline, video), name="openrouter-video"))
    if audio is not None:
        tasks.append(asyncio.create_task(prepare_audio(deadline, audio), name="openrouter-audio"))
    try:
        return list(await asyncio.gather(*tasks)) if tasks else []
    except BaseException:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        raise


class OpenRouterSimple:
    """Bounded multimodal context in, text only out."""

    @classmethod
    def INPUT_TYPES(cls):
        cached = CATALOG.cached_ids()
        model_values = [CHOOSE_MODEL, *cached] if cached else ["Loading OpenRouter models…"]
        return {
            "required": {
                "model": (model_values, {"default": model_values[0]}),
                "reasoning_effort": (
                    ["auto", "none", "minimal", "low", "medium", "high", "xhigh", "max"],
                    {"default": "auto"},
                ),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": "fixed"},
                ),
                "timeout_seconds": (
                    "INT",
                    {"default": 120, "min": 1, "max": 3600, "step": 1, "display": "number"},
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01, "round": 0.01},
                ),
                "max_tokens": (
                    "INT",
                    {"default": 4096, "min": 1, "max": 1_000_000, "step": 1, "display": "number"},
                ),
                "response_format": (["text", "json_object"], {"default": "text"}),
                "zdr": ("BOOLEAN", {"default": False}),
                "system_prompt": (
                    "STRING",
                    {"multiline": True, "default": "You are a helpful assistant."},
                ),
                "user_prompt": (
                    "STRING",
                    {"multiline": True, "default": "Describe the supplied context."},
                ),
            },
            "optional": {
                "image": ("IMAGE",),
                "video": ("VIDEO",),
                "audio": ("AUDIO",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "info", "credits")
    FUNCTION = "run"
    CATEGORY = "LLM/OpenRouter"
    DESCRIPTION = "OpenRouter multimodal context node with bounded preprocessing and text-only output."

    @classmethod
    def VALIDATE_INPUTS(cls, model: str):
        if not model or model in MODEL_SENTINELS or model.startswith("—"):
            return "Choose a compatible OpenRouter model before queueing"
        return True

    @classmethod
    def IS_CHANGED(cls, **_kwargs):
        return float("nan")

    async def run(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        reasoning_effort: str,
        seed: int,
        timeout_seconds: int,
        temperature: float,
        max_tokens: int,
        response_format: str,
        zdr: bool,
        image: Any | None = None,
        video: Any | None = None,
        audio: dict[str, Any] | None = None,
    ):
        api_key = resolve_generation_key()
        if not api_key:
            raise ValueError("Set OPENROUTER_API_KEY (or legacy LLM_KEY) in the ComfyUI environment")

        deadline = NodeDeadline(float(timeout_seconds))
        try:
            snapshot = await CATALOG.get(deadline=deadline)
            selected = snapshot.by_id(model)
            if selected is None:
                raise ValueError(f"model '{model}' is absent from the current OpenRouter catalog")
            required_modalities = {"text"}
            if image is not None:
                required_modalities.add("image")
            if video is not None:
                required_modalities.add("video")
            if audio is not None:
                required_modalities.add("audio")
            if not selected.accepts(required_modalities):
                required = ", ".join(sorted(required_modalities))
                raise ValueError(f"model '{model}' does not accept every connected modality ({required})")

            media = await _prepare_media(deadline, image=image, video=video, audio=audio)
            deadline.checkpoint()
            payload, parameter_info = build_payload(
                model=selected,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                media=media,
                reasoning_effort=reasoning_effort,
                seed=seed,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                zdr=zdr,
            )
            result = await create_chat(deadline, payload, api_key)

            credits = "Credits not checked (node deadline exhausted)"
            if deadline.remaining > 0.1:
                credit_deadline = NodeDeadline(min(3.0, deadline.remaining))
                credits = await lookup_credits(credit_deadline, api_key)

            info = {
                "model": model,
                "response_id": result.response_id,
                "usage": result.usage,
                "required_modalities": sorted(required_modalities),
                "media": {item.modality: item.public_info() for item in media},
                "parameters": parameter_info,
                "model_catalog": {
                    "stale": snapshot.stale,
                    "warning": snapshot.warning,
                    "fetched_at": snapshot.fetched_at,
                },
                "elapsed_seconds": round(deadline.elapsed, 3),
            }
            return result.text, json.dumps(info, ensure_ascii=False, separators=(",", ":")), credits
        except NodeTimeoutError as exc:
            raise RuntimeError(f"OpenRouter node timed out after {timeout_seconds} seconds") from exc


NODE_CLASS_MAPPINGS = {"OpenRouterSimple": OpenRouterSimple}
NODE_DISPLAY_NAME_MAPPINGS = {"OpenRouterSimple": "OpenRouter Simple (Text Output)"}
