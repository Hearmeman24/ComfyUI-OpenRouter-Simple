# Preserve small videos and expose useful provider errors

**Type:** `bug-fix/recon` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

An already-compatible video below 10 MB is sent without being enlarged, while a rejected OpenRouter request names the upstream provider and its sanitized diagnostic instead of stopping at “Provider returned error.”

## 🎲 Riding on these assumptions

- **The historical 400 bodies cannot be recovered from ComfyUI history** — the current node discarded their nested metadata before raising. The next provider rejection will carry the new detail; the old failures can only be correlated with their model and media combination.

## 🪤 Gotchas

- Pass-through is limited to untrimmed MP4-family input with H.264 video and optional AAC audio. Other codecs, containers, or an active trim still require transcoding.
- A required transcode is budgeted against the smaller of the 10 MB cap and the source size, so the compressor cannot turn a small input into a much larger upload.
- Provider diagnostics can contain secrets, signed URLs, or inline media. They must be bounded and redacted before entering a ComfyUI exception.

## Done when

- [ ] An untrimmed compatible MP4 below 10 MB is byte-for-byte preserved and reported as not transcoded.
- [ ] Any video transcode stays below both 10 MB and the source size when the source was already below 10 MB.
- [ ] OpenRouter 400 errors surface sanitized nested provider name/detail and opt-in router metadata when available.
- [ ] Existing timeout, Stop, size-cap, and no-paid-retry behavior remains green.

## The plan

1. Add runtime regressions that fail against the current always-transcode and top-level-only error paths.
2. Expand the video probe enough to identify safe pass-through input, then cap required transcoding to a non-expanding byte budget.
3. Decode bounded nested provider diagnostics and opt into OpenRouter router metadata without adding a user-facing knob.
4. Run focused and full verification, install the green local commit, and restart ComfyUI only after confirming the queue is idle.

