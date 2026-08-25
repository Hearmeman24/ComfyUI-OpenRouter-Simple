# Reuse OpenRouter output when regeneration is off

- **Work type:** `feature/app`
- **Status:** `draft` → proceed under task-scoped authority; no material decision is unresolved
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

The OpenRouter node currently forces execution every time a workflow is queued. The requested boolean should keep that behavior when true and reuse the previous outputs when false, without reintroducing a provider seed.

## 2. Approach & Why

- The node currently returns `NaN` unconditionally from `IS_CHANGED`, so its input signature never compares equal across queues (`node.py:125-127`).
- ComfyUI includes the `IS_CHANGED` result plus every literal and upstream input in the node cache signature (`../ComfyUI/comfy_execution/caching.py:101-127`). Returning `NaN` when `regenerate=true` and `False` when it is false therefore provides the requested behavior while still rerunning after any prompt, model, media, or upstream change.
- The browser currently recognizes every ten-value saved widget array as the removed seed layout (`web/model_filter.mjs:10-18`). The new schema is also ten values, so migration must distinguish layouts by the typed positions around `response_format`, `zdr`, and `regenerate` before editing the array.

## 3. Acceptance Criteria

- [ ] `regenerate=true` forces a fresh execution and `regenerate=false` permits unchanged output reuse. → (ask: "If false, don't regenerate new output when comfyui workflow runs and simply pass it on")
- [ ] The node exposes `regenerate` as a boolean and does not send it to OpenRouter. → (ask: "a simple boolean (regenerate) true or false")
- [ ] Seed-era and seedless saved workflows migrate to the new positional schema with `regenerate=true`. → (ask: "Like a seed, but simpler. Because seed is not supported.")

## 4. Scope & Non-Goals

**In scope:** backend node contract/cache fingerprint (`node.py:67-149`), saved-widget migration (`web/model_filter.mjs:10-18`, `web/openrouter_simple.js:3-14,108-113`), contract tests (`tests/test_node_contract.py:30-180`), migration tests (`tests/test_model_filter.mjs:1-45`), and input documentation (`README.md:5-20`).

**Non-goals (explicitly NOT doing):** provider seed support, a persistent cache across ComfyUI restarts, manual cache files, cached-value preview UI, or any change to the OpenRouter payload.

## 5. Key Decisions & Constraints

- **Decided:** default `regenerate` to true so existing workflows retain the current always-run behavior (`node.py:125-127`).
- **Constraint / must-not-break:** changing any node/upstream input while regeneration is false must invalidate the cached result because ComfyUI includes all inputs and ancestors in its signature (`../ComfyUI/comfy_execution/caching.py:101-127`).
- **Constraint / must-not-break:** the local execution control must not enter `build_payload`, whose arguments are currently provider-facing inference controls only (`node.py:182-191`).
- **Scale:** one cached output tuple per executed node under ComfyUI's configured cache → no custom storage or unbounded project-owned cache.

## 6. Code Surface Map

- `node.py:67-149` — required widget contract, cache fingerprint, run signature.
- `web/model_filter.mjs:10-18` — positional workflow migration.
- `web/openrouter_simple.js:3-14,108-113` — migration hookup during restore.
- `tests/test_node_contract.py:30-180` — Python-facing node contract and request seam.
- `tests/test_model_filter.mjs:1-45` — browser migration behavior.
- `README.md:5-20` — user-visible input behavior.

## 7. Ultracode Dispatch Notes

**Build first (sequential — freezes interfaces before any parallelism):**
- Freeze new widget order as model, reasoning, timeout, temperature, max tokens, response format, ZDR, regenerate, system prompt, user prompt.

**Parallel slices:**
- None. Backend and frontend both define one positional schema and must be changed serially as one coherent slice.

**⛓ Collision audit:** One implementation slice owns all listed files; no shared-write collision exists.

**Each agent must:** implement the slice, add red-capable tests, and self-verify against §3.

```yaml
dispatch:
  frozen: ["openrouter_simple/payload.py", "openrouter_simple/client.py", "openrouter_simple/media.py"]
  slices:
    - {key: regenerate_control, writes: ["node.py", "web/model_filter.mjs", "web/openrouter_simple.js", "tests/test_node_contract.py", "tests/test_model_filter.mjs", "README.md"]}
  testRunner: "./scripts/verify fast"
```

## 8. Assumptions & Open Questions

None. The requested behavior maps directly to ComfyUI's documented-in-code cache fingerprint seam.
