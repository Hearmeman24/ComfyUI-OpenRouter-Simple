# UI Review — OpenRouter Simple node

**Context:** make OpenRouter multimodal text inference compact and predictable · ComfyUI desktop canvas · implementation review
**Reviewed:** live ComfyUI dark-mode canvas at 93–145% zoom, including the initial node and first/second image-cable transitions, plus the declared widget order and browser state logic.

## 1. Overall diagnosis

The node deliberately inherits ComfyUI's native component styling, so it avoids adding visual noise or a second design language. Its progressive media sockets keep the default node compact while making repeated inputs discoverable through the normal cable interaction. The controls remain legible above the multiline prompt editors, although a fully populated nine-media node will necessarily become taller.

## 2. Top issues

1. **[Critical, fixed]** The reference buries model and inference controls under a very tall prompt editor — *node body* — users cannot verify the paid model immediately before queueing.
2. **[Critical, fixed]** A catalog outage previously shared the same message as a valid empty compatibility intersection — *model combo* — users could not distinguish “retry later” from “no model supports these cables.”
3. **[Polish, fixed]** The model combo did not expose whether its list was live or stale — *model label* — cached compatibility could look current.
4. **[Polish, fixed]** Declaring nine backend sockets could have made every new node visually dense — *media inputs* — the canvas now starts with one socket per modality and reveals only the next available socket.

## 3. Detailed review

- **Layout:** Controls precede system/user text areas. The live node starts with `image`, `video`, and `audio`; connecting `image` revealed `image_2`, and connecting that revealed `image_3` with no fourth socket.
- **Visual hierarchy:** The selected paid model is the first widget; prompts remain the largest editing surfaces but no longer hide the decision-driving settings.
- **Typography:** Native ComfyUI labels and textarea typography are preserved; no extra type scale is introduced.
- **Spacing & alignment:** Native widget rows preserve the host application's dense rhythm and aligned socket labels at both fit-view and 145% zoom.
- **Color:** No custom accent, gradient, glow, status tint, or competing node color is added.
- **Components:** Only native combo, numeric, boolean, and multiline widgets are used. Cable-driven filtering mutates combo values without inventing a custom control.
- **States:** Loading, no-compatible-model, catalog-error, and cached-metadata states have distinct text. Catalog error gets one bounded retry; success is represented by valid model options and node outputs.
- **Responsiveness:** ComfyUI canvas nodes are desktop controls, not mobile pages. Fit View kept the default node readable; canvas zoom and node resize behavior remain native.
- **Accessibility:** Persistent widget labels are retained. Keyboard/focus behavior is inherited from ComfyUI; the dynamic value replacement must be checked with keyboard navigation in a live render.
- **Product clarity:** The title says “Text Output”; outputs are text/info/credits only; generation-oriented image controls and outputs are absent.

## 4. Recommended fixes

1. `node.py` — keep widget order: model/reasoning/timeout/temperature/max tokens/format/ZDR, then system and user prompts.
2. `web/openrouter_simple.js` — preserve distinct loading, compatible-count, cached, empty, and catalog-error labels; never replace an invalid selection with a paid model.
3. Live ComfyUI check — confirm the two textareas start at a compact native height and remain manually resizable.
4. `web/openrouter_simple.js` — retain one empty successor per modality, never remove linked restored sockets, and cap each modality at three.

## 5. Before-shipping checklist

- [x] Model and inference controls appear before multiline prompt editors in the declared node contract.
- [x] Loading, empty, error, cached, and normal model-list states are distinct in code and tests.
- [x] An invalid prior model resets to a choose-model sentinel, not another paid model.
- [x] Render the node in ComfyUI dark mode and inspect the initial, first-image, and second-image progressive states.
- [ ] Inspect video+image, all-media, cached, and catalog-error states in a user-driven ComfyUI workflow.
- [ ] Verify keyboard selection and focus after a cable changes the model options.

## 6. Optional polish

- After a live render, consider a short node subtitle only if the “Text Output” title and socket names are still ambiguous. Do not add badges, icons, or custom color unless the native hierarchy proves insufficient.

## 7. Final implementation prompt

```text
Review the live OpenRouter Simple ComfyUI node without redesigning it. Verify controls remain above the two prompt editors; each media kind starts with one socket, reveals one empty successor after connection, and stops at three; loading, compatible-count, cached, empty, and catalog-error model states are legible; and cable changes never silently select a paid model. Test keyboard focus after each cable transition and inspect dark-mode contrast at a narrow node width. Change only defects observed in the live render, keep native ComfyUI widgets, and rerun ./scripts/verify full.
```
