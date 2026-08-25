# A simple, stoppable OpenRouter text node for ComfyUI

**Type:** `feature/app` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

One compact OpenRouter node accepts text plus at most one image, video, and audio input, shows only text-output models compatible with every connected medium, and always finishes as success, a clear error, a timeout, or a normal ComfyUI interruption.

## 🎲 Riding on these assumptions

- **Target ComfyUI is v0.32.0 or newer** — older releases may not expose the native `VIDEO` input contract used here. (confirmed only against local v0.32.0 source and the current checkout)
- **Target pods provide `ffmpeg` and `ffprobe`** — without them, image-only and text-only requests still work, while video/audio inputs fail immediately with installation guidance. (confirmed locally, not on every target pod)

## 🪤 Gotchas

- `max_tokens` is one total output budget: hidden reasoning and visible completion draw from the same allowance. The request uses `max_completion_tokens` when the selected model advertises it, otherwise legacy `max_tokens`.
- The 1 MB / 10 MB / 1 MB caps are measured on the compressed binary before base64 expansion. A media item that cannot be brought under its cap fails before any paid request is sent.
- Filtering in the browser is convenience, not trust: the backend rechecks the selected model against connected modalities before preprocessing and submission.
- ZDR is opt-in and only sends OpenRouter's `provider.zdr`; no other provider-routing controls are exposed.

## Done when

- [ ] One node provides system prompt, user prompt, model, reasoning effort, seed, timeout, temperature, unified `max_tokens`, response format, ZDR, and optional image/video/audio inputs.
- [ ] Model choices update to the intersection of all connected modalities, and an invalid prior selection is never silently replaced with a paid alternative.
- [ ] Images are at most 1 MB, videos at most 10 MB, and audio at most 1 MB before upload, using quality-preserving encoding and Lanczos-class scaling where spatial resizing is needed.
- [ ] The only generated output is text, with separate info and credits strings.
- [ ] Timeouts, Stop, HTTP rejection, malformed responses, and unavailable model metadata all reach a bounded terminal state without leaving requests or encoders running.
- [ ] Automated tests prove modality intersection, payload construction, compression caps, deadline behavior, interruption cleanup, redaction, and non-fatal credits lookup.

## The plan

1. Freeze the model metadata, request, media, and cancellation contracts in small backend modules.
2. Build the async node and local media preparation pipeline, then add the frontend model intersection filter.
3. Exercise the node against local fake HTTP endpoints and generated media fixtures; do not make a paid OpenRouter call.
4. Document installation, secrets, limits, and the exact unsupported surfaces.
