# Progressive media inputs, up to three of each kind

- **Work type:** `feature/app`
- **Status:** `draft` → proceed under task-scoped authority; no material decision remains unresolved
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

The node currently declares and accepts exactly one optional `image`, `video`, and `audio` input (`node.py:85-89`, `node.py:108-145`). Its frontend model filter recognizes only those three exact names (`web/model_filter.mjs:1-14`), so adding sockets only in the browser would fail backend prompt validation and execution.

OpenRouter Chat Completions already serializes media as repeated content-array entries (`openrouter_simple/payload.py:9-20`). The missing contract is named multi-input collection, progressive socket presentation, and per-socket reporting rather than a new wire format.

## 2. Approach & Why

- Declare all nine optional backend keys so ComfyUI validation has an authoritative schema, while the browser initially hides the six trailing keys and restores them progressively (`node.py:47-90`).
- Preserve legacy base names `image`, `video`, and `audio`; this keeps existing workflow links and execution arguments valid (`node.py:120-145`).
- Normalize suffixed names to their base modality for filtering; the catalog advertises modality sets, not attachment counts (`openrouter_simple/models.py:20-39`, `web/model_filter.mjs:6-24`).
- Carry `(socket_name, PreparedMedia)` pairs through preprocessing so duplicate modalities do not overwrite the current info dictionary (`node.py:166-172`).
- Keep one shared deadline and the existing cancel-all-on-first-failure behavior while expanding the task collection (`node.py:19-41`).

## 3. Acceptance Criteria

- [ ] One visible socket per modality grows to two, then three, only as the previous slots are populated. → (ask: “if I connect an image input, expose another one”)
- [ ] The node accepts at most three images, three videos, and three audio clips, nine total. → (ask: “Up to 3 per media item and 9 total”)
- [ ] Every populated socket is locally prepared and included as its own Chat Completions content entry. → (ask: “Audio / Video / Image inputs should increment as populated”)
- [ ] Model filtering continues to require the intersection of connected modality kinds, regardless of how many of each are connected. → (ask: original modality-filter behavior plus the new repeated sockets)
- [ ] Existing workflows using only `image`, `video`, and/or `audio` remain valid. → (ask: “A few more fixes” to the installed node, not a replacement node)
- [ ] Direct live validation uses media from `/Users/avivkaplan/Dump`, after an exact payload and pricing envelope is shown, and never submits through ComfyUI. → (ask: “clearance to test against live openrouter models with media from /Users/avivkaplan/Dump”)

## 4. Scope & Non-Goals

**In scope:** `node.py`, `web/openrouter_simple.js`, `web/model_filter.mjs`, backend/frontend/payload tests, README, historical spec, real ComfyUI visual inspection, and bounded direct OpenRouter validation.

**Non-goals (explicitly NOT doing):** no more than three of any modality, no PDFs/files, no media generation, no per-provider count database, no silent attachment dropping, no retry of paid POSTs, no ComfyUI prompt submission, and no remote publication.

## 5. Key Decisions & Constraints

- **Decided:** socket IDs are `image`, `image_2`, `image_3`, `video`, `video_2`, `video_3`, `audio`, `audio_2`, `audio_3`; the legacy names remain slot one (`node.py:85-89`).
- **Decided:** payload order is images 1-3, videos 1-3, then audio 1-3, with absent sockets skipped; `_user_content` already preserves the list order it receives (`openrouter_simple/payload.py:9-20`).
- **Decided:** the UI retains every connected socket plus one empty successor, capped at three; it removes only unlinked surplus sockets.
- **Constraint / must-not-break:** backend modality compatibility remains authoritative before preprocessing (`node.py:130-145`).
- **Constraint / must-not-break:** all media completes before the paid POST and any failure cancels sibling work (`node.py:19-41`, `node.py:145-159`).
- **Constraint / must-not-break:** text-only output remains hardcoded (`openrouter_simple/payload.py:40-44`).
- **Scale:** one personal ComfyUI execution with at most nine media items; preprocessing stays bounded by the existing per-item caps and one total deadline.

## 6. Code Surface Map

- `node.py:19-41` — preparation task ownership and cancellation.
- `node.py:47-180` — public socket schema, compatibility, payload handoff, and info output.
- `web/openrouter_simple.js:35-97` — node lifecycle hooks and live model refresh.
- `web/model_filter.mjs:1-29` — pure media-name normalization and model intersection seam.
- `openrouter_simple/payload.py:9-44` — repeated ordered content serialization and text-only output.
- `tests/test_node_contract.py:25-48` — public backend schema regression.
- `tests/test_model_filter.mjs:20-42` — pure browser behavior regression.
- `tests/test_payload.py:17-41` — multimodal content regression.

## 7. Ultracode Dispatch Notes

**Build first (sequential — freezes interfaces before any parallelism):**

- Freeze socket names, ordered media collection, and progressive visibility behavior in tests before implementation.

**Parallel slices:** none. Backend schema and frontend serialization are a single small compatibility contract.

**⛓ Collision audit:** no fan-out; the primary session owns every touched file.

```yaml
dispatch:
  frozen:
    - openrouter_simple/media.py
    - openrouter_simple/client.py
    - openrouter_simple/models.py
  slices: []
  testRunner: "PYTHON_BIN=/Users/avivkaplan/src/comfy/ComfyUI/venv/bin/python ./scripts/verify fast"
```

## 8. Assumptions & Open Questions

- **ASSUMPTION:** no universal OpenRouter model/provider contract guarantees three inputs of every modality in one request; current OpenRouter documentation explicitly says file counts vary by provider and model. Impact if wrong: a future catalog count-capability field could support stricter filtering, but today the node must surface provider rejection rather than infer it.

