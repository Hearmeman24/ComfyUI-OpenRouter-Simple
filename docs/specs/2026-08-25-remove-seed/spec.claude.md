# Remove the OpenRouter seed control

- **Work type:** `bug-fix/recon`
- **Status:** `draft` — proceed under task-scoped authority; no material decision is unresolved
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

ComfyUI generated seed `471994551739533`; Google AI Studio rejected the request because `generation_config.seed` is `TYPE_INT32`. The requested outcome is to remove seed as redundant.

## 2. Root Cause / Mechanism

- The node declares seed as an unsigned 64-bit-range integer widget, so normal ComfyUI seed randomization can exceed provider-specific ranges. — evidence: `node.py:77-80`
- The run method passes that value into payload construction without provider-range normalization. — evidence: `node.py:133-144`, `node.py:187-198`
- The payload builder sends any integer whenever model metadata advertises seed support. — evidence: `openrouter_simple/payload.py:23-35`, `openrouter_simple/payload.py:63-67`
- The frontend already owns a configure hook, which is the correct seam to remove the legacy positional widget value before restoration. — evidence: `web/openrouter_simple.js:95-112`
- Confirmed by repro: a local payload probe with the reported value emitted `471994551739533` unchanged; the user-supplied live trace shows Google rejected that exact value as `TYPE_INT32`.

## 3. Acceptance Criteria

- [ ] The node no longer displays or accepts seed, and Google requests cannot fail because this node supplied an out-of-range seed. → (ask: "Remove seed, it's redundant")
- [ ] Payloads and parameter diagnostics never contain seed even when model metadata advertises support. → (ask: "Remove seed")
- [ ] Pre-removal saved nodes retain the correct timeout, temperature, token, format, ZDR, and prompt values after loading. → (ask: "Remove seed")

## 4. Scope & Non-Goals

**In scope:** `node.py`, `openrouter_simple/payload.py`, `web/openrouter_simple.js`, `web/model_filter.mjs`, their tests, README/UI documentation, and this historical spec.

**Non-goals:** No provider-specific seed clamping, retry-on-400 behavior, changes to other inference controls, or paid live request.

## 5. Key Decisions & Constraints

- **Decided:** Delete seed rather than clamp it; this follows the user's explicit request and avoids provider-specific range policy.
- **Constraint / must-not-break:** Existing saved workflows use positional `widgets_values`; migration must remove only the legacy third value before the original configure method runs.
- **Mirror existing:** `web/openrouter_simple.js:107-112` remains the single configure hook.

## 6. Code Surface Map

- `node.py:67-115` — authoritative ComfyUI input schema.
- `node.py:133-199` — runtime signature and payload call.
- `openrouter_simple/payload.py:23-90` — request and parameter-info serialization.
- `web/openrouter_simple.js:95-123` — node lifecycle hooks.
- `tests/test_node_contract.py:36-67` — exact public input contract.
- `tests/test_payload.py:19-62` — approved request controls.

## 7. Ultracode Dispatch Notes

**Build first (sequential):** Add red tests defining the no-seed contract and legacy-array migration.

**Parallel slices:** None. Python, frontend migration, tests, and docs form one small serialized contract change.

**⛓ Collision audit:** One slice owns every touched seed surface; no concurrent writers.

```yaml
dispatch:
  frozen: []
  slices:
    - {key: removeSeed, writes: [node.py, openrouter_simple/payload.py, web/openrouter_simple.js, web/model_filter.mjs, tests/test_node_contract.py, tests/test_payload.py, tests/test_model_filter.mjs, README.md, docs/ui-review.md]}
  testRunner: "./scripts/verify fast"
```

## 8. Assumptions & Open Questions

None. The failing value, error contract, current serialization path, and saved-workflow migration seam are verified.
