# A simple, stoppable OpenRouter text node for ComfyUI

- **Work type:** `feature/app`
- **Status:** `draft` → proceed under task-scoped authority; no material decision remains unresolved
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

The user needs a smaller OpenRouter ComfyUI node that keeps the controls which materially affect text inference, accepts multimodal context, and cannot leave a workflow stuck. The existing installed reference adds image sockets in browser code and uses a connection callback, but its surface and execution path are not the desired contract (`/Users/avivkaplan/src/comfy/ComfyUI/custom_nodes/ComfyUI-Openrouter_node/web/openrouter_dynamic_inputs.js:22-54`).

The new node is a standalone custom-node repository. It sends only Chat Completions requests whose requested output modality is text. Optional image, video, and audio are input context only; there are no media-generation inputs, endpoints, or outputs.

## 2. Approach & Why

- **Use a native async V1 node function.** ComfyUI detects coroutine node functions and schedules/awaits them instead of blocking the execution thread (`/Users/avivkaplan/src/comfy/ComfyUI/execution.py:289-303`). This lets the node race HTTP/subprocess work against a deadline and the shared Stop flag.
- **Use ComfyUI's interruption semantics.** The server's `/interrupt` route calls `nodes.interrupt_processing()` (`/Users/avivkaplan/src/comfy/ComfyUI/server.py:1160-1188`), while `throw_exception_if_processing_interrupted()` raises ComfyUI's native interruption exception (`/Users/avivkaplan/src/comfy/ComfyUI/comfy/model_management.py:2098-2122`). The node will poll the flag, cancel its active work, clean up, then raise through the native helper.
- **Stream video into a cancellable encoder.** Native video inputs expose `get_stream_source()` and permit file-backed implementations to avoid a full in-memory copy (`/Users/avivkaplan/src/comfy/ComfyUI/comfy_api/latest/_input/video_types.py:57-71`). Audio arrives as the established waveform/sample-rate dictionary; the local conversion utility documents shape `(1, channels, samples)` (`/Users/avivkaplan/src/comfy/ComfyUI/comfy_api_nodes/util/conversions.py:261-282`).
- **Filter twice.** Browser-side `onConnectionsChange` is an established extension seam (`/Users/avivkaplan/src/comfy/ComfyUI/custom_nodes/ComfyUI-Openrouter_node/web/openrouter_dynamic_inputs.js:52-54`), but the backend remains authoritative. A stale or hand-edited workflow cannot submit an incompatible model.
- **Fetch model metadata once, filter locally.** The backend route returns a normalized, text-output-only snapshot from OpenRouter's Models API. The frontend computes set inclusion for `text` plus connected `image`, `video`, and `audio`; it does not issue a remote request on every cable event.

## 3. Acceptance Criteria

- [ ] A single ComfyUI node exposes system prompt, user prompt, reasoning effort, compatible model list, seed, timeout, temperature, unified `max_tokens`, response format (`text` or `json_object`), ZDR, and optional one-each IMAGE/VIDEO/AUDIO sockets. → (ask: "The node should have…" and "I agree to add…")
- [ ] Connecting image, video, audio, or any combination immediately reduces the model combo to text-output models whose input modalities are a superset of every connected modality; disconnecting restores eligible options. → (ask: "filter the list as soon as an input is connected")
- [ ] If the selected model becomes invalid, the UI shows a choose-compatible-model sentinel and the backend refuses execution; it never silently chooses another paid model. → (ask: "only show models that actually accept…")
- [ ] Images are encoded to WebP and kept at or below 1,000,000 bytes; quality is reduced before dimensions, and spatial downscaling preserves aspect ratio with Pillow Lanczos. → (ask: "Images resized down to 1MB" and "Attempt to use lanczos")
- [ ] Videos are kept or transcoded to MP4/H.264/AAC at or below 10,000,000 bytes with bitrate derived from duration; spatial fallback uses ffmpeg's Lanczos scaler. → (ask: "Videos resized down to 10MB")
- [ ] Audio is encoded to MP3 at or below 1,000,000 bytes with duration-derived bitrate and high-quality resampling only when needed. → (ask: "Audio resized down to 1MB")
- [ ] All local preprocessing finishes before the request is submitted and no oversize media reaches OpenRouter. → (ask: "process them in the background before sending")
- [ ] The request hardcodes text output and the node returns only `text`, `info`, and `credits` strings; unexpected media-only responses are rejected. → (ask: "Do not allow for image/video/voice generation… text output only" and "Show credits output")
- [ ] `max_tokens` represents the total model output allowance, including reasoning; the adapter prefers `max_completion_tokens` and falls back to `max_tokens` only when model metadata advertises the legacy parameter. → (ask: "max_tokens (combining reasoning and completion maybe?)")
- [ ] The node has a total preprocessing-plus-chat deadline, no blind POST retry, bounded error-body reads, redacted messages, and a separately bounded non-fatal credits lookup. → (ask: "resilient and gracefully handle timeouts and rejections")
- [ ] Pressing ComfyUI Stop cancels the active HTTP body read or encoder process, removes temporary files, and surfaces as a native interrupted execution within one second in tests. → (ask: "ComfyUI stop button should also stop the running node")
- [ ] A stalled local endpoint and a non-terminating fake encoder both prove bounded cancellation with no live child process or pending asyncio task after cleanup. → (ask: "never hang or make the ComfyUI workflow stuck")

## 4. Scope & Non-Goals

**In scope:** one standalone custom-node package; an async OpenRouter client; normalized model metadata and cache; local image/video/audio compression; a small frontend extension for model filtering; tests, README, and verification script.

**Non-goals (explicitly NOT doing):** image/video/audio generation; tools/functions; web search; PDFs/files; chat history; multiple attachments per modality; streaming partial text; custom JSON schemas; top-p/top-k/min-p/frequency/presence/repetition penalties; logprobs; provider ordering/price/latency routing; fallback model lists; transforms; plugins; raw API-key widgets; retries of paid POST requests; deployment, push, or a paid live request.

## 5. Key Decisions & Constraints

- **Decided:** one node, one attachment per modality, one visible output-budget control. The budget includes reasoning and completion; there is no second reasoning-token budget.
- **Decided:** response format is `text` or `json_object`; JSON Schema is excluded because it adds a schema input the user did not approve.
- **Decided:** ZDR defaults false and maps only to `provider: {"zdr": true}` when enabled.
- **Decided:** generation auth resolves `OPENROUTER_API_KEY`, then `LLM_KEY`; the workflow never serializes a secret widget.
- **Decided:** account credits use optional `OPENROUTER_MANAGEMENT_KEY`; otherwise the generation key's `/key` limit is reported and labeled as a key limit, never as account credit.
- **Constraint / must-not-break:** the chat POST has no automatic retry because repeating an ambiguous request can spend twice.
- **Constraint / must-not-break:** media caps apply to the binary bytes before base64; the info output reports source/compressed byte counts and applied/omitted model parameters without prompts or secrets.
- **Constraint / must-not-break:** no raw exception, authorization header, prompt, data URL, or signed query string appears in errors or logs.
- **Mirror existing:** async execution scheduling from `/Users/avivkaplan/src/comfy/ComfyUI/execution.py:292-303`; interrupt racing/cleanup shape from `/Users/avivkaplan/src/comfy/ComfyUI/comfy_api_nodes/util/client.py:694-757`; connection updates from `/Users/avivkaplan/src/comfy/ComfyUI/custom_nodes/ComfyUI-Openrouter_node/web/openrouter_dynamic_inputs.js:52-134`.
- **Scale:** personal ComfyUI workflows with at most one image, one video, and one audio attachment per execution. Memory and subprocess use must remain bounded by streaming/temp files and the explicit byte caps.

## 6. Code Surface Map

Existing grounded surfaces:

- `/Users/avivkaplan/src/comfy/ComfyUI/execution.py:243-303` — async node invocation.
- `/Users/avivkaplan/src/comfy/ComfyUI/comfy/model_management.py:2098-2122` — native interruption state and exception.
- `/Users/avivkaplan/src/comfy/ComfyUI/comfy_api/latest/_input/video_types.py:25-71` — video save/stream interface.
- `/Users/avivkaplan/src/comfy/ComfyUI/comfy_api_nodes/util/conversions.py:261-306` — audio tensor shape and MP3 encoding analog.
- `/Users/avivkaplan/src/comfy/ComfyUI/custom_nodes/ComfyUI-Openrouter_node/web/openrouter_dynamic_inputs.js:22-134` — frontend extension and cable-change hook.

Planned new surfaces:

- `__init__.py`, `node.py` — ComfyUI registration and the public node contract.
- `openrouter_simple/client.py` — bounded HTTP, payload/response handling, credits, error sanitization.
- `openrouter_simple/models.py` — model metadata normalization, compatibility and parameter support.
- `openrouter_simple/media.py` — byte caps and cancellable encoders.
- `openrouter_simple/cancellation.py` — shared deadline/interrupt/subprocess lifecycle.
- `web/openrouter_simple.js` — metadata fetch and connection-aware combo filtering.
- `tests/` — unit and local integration coverage.
- `README.md`, `requirements.txt`, `pyproject.toml`, `scripts/verify` — installation and validation surface.

## 7. Ultracode Dispatch Notes

**Build first (sequential — freezes interfaces before any parallelism):**

- Define normalized model metadata, prepared-media records, request result, deadline/interrupt behavior, and node input/output names.

**Parallel slices:** none. The backend, frontend serialization, and tests share the same small public contract, so this implementation remains serial in the primary session.

**⛓ Collision audit:** no fan-out; one Git writer owns every new path.

```yaml
dispatch:
  frozen:
    - /Users/avivkaplan/src/comfy/ComfyUI
    - /Users/avivkaplan/src/comfy/ComfyUI/custom_nodes/ComfyUI-Openrouter_node
  slices: []
  testRunner: "./scripts/verify fast"
```

## 8. Assumptions & Open Questions

- **ASSUMPTION:** deployment targets run ComfyUI v0.32.0 or newer. This was verified against the local v0.32.0 source and current v0.33 checkout, not every deployed pod. Impact if wrong: native `VIDEO` sockets may not load and the README minimum version must be raised or a legacy adapter added.
- **ASSUMPTION:** deployment targets provide executable `ffmpeg` and `ffprobe`. They exist locally, but no remote pod was inspected. Impact if wrong: text/image requests work, while video/audio fail immediately with an actionable dependency error.
- **OPEN QUESTION (non-blocking):** OpenRouter provider/model support changes over time. The node treats live model metadata as authoritative and preserves a stale cache for availability; no static model compatibility list is promised.
