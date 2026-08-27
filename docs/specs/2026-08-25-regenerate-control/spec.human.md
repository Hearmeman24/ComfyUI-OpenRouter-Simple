# Reuse OpenRouter output when regeneration is off

**Type:** `feature/app` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

The node has a `regenerate` boolean. `true` makes a fresh OpenRouter request whenever the workflow is queued; `false` reuses ComfyUI's cached text, info, and credits outputs while this node and its upstream inputs are unchanged.

## 🪤 Gotchas

- Turning `regenerate` off is ComfyUI caching, not permanent storage: changing a prompt, model, media input, or another upstream input invalidates the cached output and runs the node once again.
- Old workflows exist in both seed-era and seedless positional widget layouts. Both must migrate to `regenerate=true`, preserving the old always-run behavior and leaving prompt values in their correct widgets.

## Done when

- [ ] `regenerate=true` forces a fresh execution and `regenerate=false` permits unchanged output reuse.
- [ ] The control is a simple boolean and is never sent to OpenRouter.
- [ ] Existing seed-era and seedless saved workflows restore without shifted widget values and default to `regenerate=true`.
- [ ] The local ComfyUI node visibly exposes the control without making a live generation request.

## The plan

1. Add red contract tests for the boolean, cache fingerprint, and both saved-workflow migrations.
2. Implement the backend cache toggle and typed frontend migration as one serialized slice.
3. Update the README, run fast/full verification, and inspect the node in local ComfyUI without queueing it.
4. Commit the release-ready change and update the local installed node; public push/publish remains a separate explicit release action.

