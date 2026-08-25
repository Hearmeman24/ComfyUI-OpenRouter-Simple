# ComfyUI OpenRouter Simple

One OpenRouter node for multimodal context in and text only out. It keeps the useful inference controls, filters the model list to the exact combination of connected inputs, compresses media locally before submission, and treats timeout/Stop as real cancellation rather than a background request that keeps running.

## What the node exposes

| Input | Behavior |
| --- | --- |
| `system_prompt` | Optional system instruction. |
| `user_prompt` | The user message sent with any connected media. |
| `model` | Live OpenRouter text-output models, filtered by connected modalities. |
| `reasoning_effort` | `auto`, `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, or `max`. Unsupported explicit reasoning fails before submission. |
| `seed` | Sent only when the selected model advertises `seed`; otherwise reported as omitted in `info`. |
| `timeout_seconds` | One deadline for catalog refresh, preprocessing, and the chat request. Credits use only time still left, capped at 3 seconds. |
| `temperature` | Sent only when supported by the selected model. |
| `max_tokens` | One total output budget shared by hidden reasoning and visible completion. It maps to `max_completion_tokens` when available, then legacy `max_tokens`. |
| `response_format` | `text` or `json_object`. JSON fails before submission when the model does not advertise structured output support. |
| `zdr` | Off by default. When enabled, sends only `provider.zdr: true`. |
| `image` / `video` / `audio` | Optional one-each context inputs. They never become generation outputs. |

Outputs are `text`, compact JSON `info`, and `credits`. There are no IMAGE, VIDEO, or AUDIO outputs and the request hardcodes `modalities: ["text"]`.

## Install

Requires ComfyUI v0.32.0 or newer, Python 3.10+, and `ffmpeg`/`ffprobe` for video or audio inputs.

```bash
cd ComfyUI/custom_nodes
git clone <repository-url> ComfyUI-OpenRouter-Simple
python -m pip install -r ComfyUI-OpenRouter-Simple/requirements.txt
```

Restart ComfyUI, then add **LLM → OpenRouter → OpenRouter Simple (Text Output)**.

Set the generation key in ComfyUI's environment; there is deliberately no key widget saved into workflow JSON:

```bash
export OPENROUTER_API_KEY="your-generation-key"
```

Legacy `LLM_KEY` is accepted second. An optional `OPENROUTER_MANAGEMENT_KEY` enables true account-credit lookup. Without it, the `credits` output reports the generation key's `limit_remaining` from `/key` and labels it as an API-key limit—not account credit.

## Media preparation

The limits are decimal bytes measured before base64:

- IMAGE: WebP, at most 1,000,000 bytes. Quality is reduced before dimensions; spatial fallback preserves aspect ratio with Pillow Lanczos.
- VIDEO: MP4/H.264/AAC, at most 10,000,000 bytes. An untrimmed compatible MP4 already below the cap is preserved byte-for-byte. Required conversion or trimming uses a two-pass budget derived from duration and capped at the smaller of 10 MB and the source size, so preparation never enlarges an under-limit video. Spatial fallback uses ffmpeg Lanczos and only lowers frame rate when the available bitrate is unusually small.
- AUDIO: MP3, at most 1,000,000 bytes. Bitrate is derived from duration; SoXr is preferred, with high-precision FFmpeg SWR fallback when SoXr is unavailable.

Connected media are prepared concurrently in temporary directories. The chat POST does not begin until every input is below its cap. A media item that cannot safely reach its cap fails locally, before a paid request.

## Model filtering

The backend fetches OpenRouter's model metadata, keeps only models whose output modalities include text, and caches the normalized snapshot. The browser computes this intersection whenever a media cable changes:

```text
required = text + every connected one of image/video/audio
eligible = required ⊆ model.input_modalities
```

The current selection is retained only if it remains eligible. Otherwise the node returns to **choose a compatible OpenRouter model**; it never silently changes to another paid model. The backend repeats the same compatibility check before preprocessing.

If live metadata is unavailable, a prior disk cache is used and marked stale. With no live or cached catalog, execution stops clearly rather than guessing that a media model is compatible.

## Cancellation and failures

- ComfyUI Stop is polled at 100 ms or less during HTTP and encoder work.
- Active HTTP tasks are cancelled and their sessions closed.
- Active ffmpeg/ffprobe children receive terminate, then kill after a bounded grace period, and are reaped.
- Temporary directories are removed on success, rejection, timeout, and Stop.
- The paid chat POST is never automatically retried, avoiding ambiguous double spend.
- Error bodies are capped and secrets, bearer tokens, and URL query strings are redacted.
- Provider rejections surface sanitized nested provider diagnostics and opt-in router metadata when OpenRouter supplies them; inline media remains redacted.
- Credits failure is non-fatal after a successful text completion.

OpenRouter rejections remain normal ComfyUI execution errors. Stop uses ComfyUI's native interruption exception, so it is shown as an interrupted workflow rather than a fabricated API failure.

## Deliberately excluded

This node does not expose tools/functions, web search, PDFs/files, chat history, multiple attachments per modality, streaming partial text, JSON Schema, top-p/top-k/min-p, penalties, logprobs, provider ordering, price/latency routing, fallback models, transforms, plugins, or media generation.

## OpenRouter contracts used

- [Chat Completions request](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)
- [Reasoning tokens and effort](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
- [Model metadata](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties)
- [Provider routing and ZDR](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Router metadata for diagnostics](https://openrouter.ai/docs/guides/features/router-metadata)
- [Image inputs](https://openrouter.ai/docs/guides/overview/multimodal/image-understanding)
- [Video inputs](https://openrouter.ai/docs/guides/overview/multimodal/videos)
- [Audio inputs](https://openrouter.ai/docs/guides/overview/multimodal/audio)
- [Account credits](https://openrouter.ai/docs/api/api-reference/credits/get-remaining-credits) and [current API key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key)

## Verification

```bash
./scripts/verify fast
./scripts/verify full
```

`fast` covers the public contract, model intersection, payload mapping, stalled HTTP deadline, rejection redaction, credits failure, and real child-process cancellation. `full` also generates and compresses image, video, and audio fixtures. Set `PYTHON_BIN` if ComfyUI uses a non-default Python.

No verification command makes a paid OpenRouter request. Local fake endpoints exercise the HTTP boundary.

## Architecture and operational boundary

- `node.py` owns the ComfyUI input/output contract and request lifecycle.
- `openrouter_simple/models.py` owns live metadata normalization and the stale cache.
- `openrouter_simple/media.py` owns exact pre-base64 caps and encoder selection.
- `openrouter_simple/cancellation.py` owns the shared deadline, Stop polling, and subprocess cleanup.
- `openrouter_simple/client.py` owns bounded OpenRouter HTTP and credits lookup.
- `web/` owns display-only live filtering; it is never authoritative for execution.

This repository is a standalone custom node. Installing it locally does not deploy it to a RunPod template, publish it to the Comfy registry, or create a remote repository. There is no project brain page yet.
