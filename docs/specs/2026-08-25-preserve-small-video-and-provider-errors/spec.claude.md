# Preserve small videos and expose useful provider errors

- **Work type:** `bug-fix/recon`
- **Status:** `draft` → proceed under task-scoped authority; no material decision remains unresolved
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

The video preparation path expands small inputs because it computes bitrate from the fixed 10 MB ceiling and always invokes two-pass H.264/AAC encoding, even when the input is already compatible and below the limit (`openrouter_simple/media.py:249-315`). A generated 148,119-byte H.264/AAC MP4 reproduced this at runtime as a 652,176-byte prepared upload (4.40x).

Separately, OpenRouter’s provider-error envelope can carry its useful upstream diagnostic below `error.metadata`, while this client returns only `error.message` (`openrouter_simple/client.py:77-84`). The user’s six recorded failures therefore all collapsed to the same generic HTTP 400 message at the raise site (`openrouter_simple/client.py:108-119`).

## 2. Root Cause / Mechanism

- Cause: `prepare_video` derives `total_bitrate` exclusively from `VIDEO_LIMIT`, then unconditionally calls `_encode_video_passes`; it has no compatibility/pass-through branch and no source-size ceiling (`openrouter_simple/media.py:249-315`).
- Confirmed by repro: yes. A local 1.5-second MP4 grew from 148,119 bytes to 652,176 bytes with no spatial resize.
- Cause: `_error_detail` reads only the top-level error message/code and drops `error.metadata.raw`, provider identity, and top-level router metadata (`openrouter_simple/client.py:77-84`).
- Confirmed by repro: yes. The local fake-response seam used by client tests currently only checks a top-level 401 message (`tests/test_client.py:43-56`), and the supplied ComfyUI history retains only the resulting generic exception rather than the discarded response body.

## 3. Acceptance Criteria

- [ ] An already-compatible, untrimmed video below 10 MB is sent byte-for-byte without enlargement. → (ask: “Agreed on the transcoding bug, fix it.”)
- [ ] A video that must be transcoded remains at or below 10 MB and does not exceed an already-under-limit source. → (ask: “fix it”)
- [ ] A provider HTTP 400 includes bounded, sanitized provider identity and nested upstream detail when OpenRouter supplies them. → (ask: supplied repeated opaque “Provider returned error” failures)
- [ ] Timeout, ComfyUI Stop, redaction, temporary cleanup, and no paid POST retry remain unchanged. → (ask: original resilience and never-hang requirements)

## 4. Scope & Non-Goals

**In scope:** video probing/preparation in `openrouter_simple/media.py`, error decoding/headers in `openrouter_simple/client.py`, their behavioral tests, README operating truth, and this historical spec.

**Non-goals (explicitly NOT doing):** no live OpenRouter or ComfyUI generation, no provider-selection knob, no automatic retry, no model-list policy change, no new modality, and no remote publication.

## 5. Key Decisions & Constraints

- **Decided:** direct pass-through requires MP4-family container, H.264 video, optional AAC audio, no active trim, and source bytes at or below the cap; the existing node contract promises MP4/H.264/AAC (`README.md:43-49`).
- **Decided:** a required encode targets `min(VIDEO_LIMIT, source_bytes)` before safety headroom rather than the fixed ceiling (`openrouter_simple/media.py:268-275`).
- **Decided:** send OpenRouter’s documented `X-OpenRouter-Metadata: enabled` request header and decode additive fields permissively; this is diagnostic behavior, not a new inference control.
- **Constraint / must-not-break:** error-body reads remain capped at 16,384 bytes (`openrouter_simple/client.py:17,108-117`).
- **Constraint / must-not-break:** the paid chat POST remains single-attempt (`openrouter_simple/client.py:102-130`).
- **Mirror existing:** keep the current deadline-wrapped `run_process` and `deadline.run` I/O boundaries (`openrouter_simple/media.py:142-155,231-246,294`).

## 6. Code Surface Map

- `openrouter_simple/media.py:142-315` — video probe, geometry, encoder, and prepared-media info.
- `openrouter_simple/client.py:35-119` — redaction, error envelope decoding, request headers, and exception construction.
- `tests/test_media_integration.py:47-76` — real ffmpeg behavioral seam.
- `tests/test_client.py:43-56` — local fake HTTP rejection seam.
- `README.md:37-66` — media and failure operating contract.

## 7. Ultracode Dispatch Notes

**Build first (sequential — freezes interfaces before any parallelism):**

- Add the two behavioral regressions, then implement both fixes serially because production and test files form one small contract.

**Parallel slices:** none.

**⛓ Collision audit:** no fan-out; the primary session owns all touched paths.

```yaml
dispatch:
  frozen:
    - web/
    - openrouter_simple/payload.py
    - openrouter_simple/models.py
  slices: []
  testRunner: "/Users/avivkaplan/src/comfy/ComfyUI/venv/bin/python -m unittest"
```

## 8. Assumptions & Open Questions

- **ASSUMPTION:** the exact nested diagnostics from the historical provider failures are unrecoverable because the response bodies were not persisted. Impact if wrong: a local durable HTTP trace could identify the earlier provider cause immediately; none was found in ComfyUI history or its current log.
