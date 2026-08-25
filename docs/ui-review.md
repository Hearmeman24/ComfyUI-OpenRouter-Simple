# UI Review — OpenRouter Simple node

**Context:** make OpenRouter multimodal text inference compact and predictable · ComfyUI desktop canvas · implementation review
**Reviewed:** the supplied reference-node screenshot plus the new node's declared widget order and browser state logic. Exact rendered spacing, contrast, and resize behavior remain unverified without launching ComfyUI.

## 1. Overall diagnosis

The node deliberately inherits ComfyUI's native component styling, so it avoids adding visual noise or a second design language. The biggest usability lever is hierarchy: model and inference controls must remain above the multiline prompt editors, rather than being pushed below a tall text area as in the supplied reference. The implemented order and explicit catalog-state labels address that structural problem without adding more knobs.

## 2. Top issues

1. **[Critical, fixed]** The reference buries model and inference controls under a very tall prompt editor — *node body* — users cannot verify the paid model immediately before queueing.
2. **[Critical, fixed]** A catalog outage previously shared the same message as a valid empty compatibility intersection — *model combo* — users could not distinguish “retry later” from “no model supports these cables.”
3. **[Polish, fixed]** The model combo did not expose whether its list was live or stale — *model label* — cached compatibility could look current.

## 3. Detailed review

- **Layout:** Controls now precede system/user text areas. Optional media sockets remain native ComfyUI inputs at the top.
- **Visual hierarchy:** The selected paid model is the first widget; prompts remain the largest editing surfaces but no longer hide the decision-driving settings.
- **Typography:** Native ComfyUI labels and textarea typography are preserved; no extra type scale is introduced.
- **Spacing & alignment:** Native widget rows preserve the host application's density and alignment. Exact pixels are unverified until rendered.
- **Color:** No custom accent, gradient, glow, status tint, or competing node color is added.
- **Components:** Only native combo, numeric, boolean, and multiline widgets are used. Cable-driven filtering mutates combo values without inventing a custom control.
- **States:** Loading, no-compatible-model, catalog-error, and cached-metadata states have distinct text. Catalog error gets one bounded retry; success is represented by valid model options and node outputs.
- **Responsiveness:** ComfyUI canvas nodes are desktop controls, not mobile pages. Node resize behavior remains native and should be visually checked at narrow canvas widths.
- **Accessibility:** Persistent widget labels are retained. Keyboard/focus behavior is inherited from ComfyUI; the dynamic value replacement must be checked with keyboard navigation in a live render.
- **Product clarity:** The title says “Text Output”; outputs are text/info/credits only; generation-oriented image controls and outputs are absent.

## 4. Recommended fixes

1. `node.py` — keep widget order: model/reasoning/seed/timeout/temperature/max tokens/format/ZDR, then system and user prompts.
2. `web/openrouter_simple.js` — preserve distinct loading, compatible-count, cached, empty, and catalog-error labels; never replace an invalid selection with a paid model.
3. Live ComfyUI check — confirm the two textareas start at a compact native height and remain manually resizable.

## 5. Before-shipping checklist

- [x] Model and inference controls appear before multiline prompt editors in the declared node contract.
- [x] Loading, empty, error, cached, and normal model-list states are distinct in code and tests.
- [x] An invalid prior model resets to a choose-model sentinel, not another paid model.
- [ ] Render the node in ComfyUI dark mode and inspect initial, image, video+image, all-media, cached, and catalog-error states.
- [ ] Verify keyboard selection and focus after a cable changes the model options.

## 6. Optional polish

- After a live render, consider a short node subtitle only if the “Text Output” title and socket names are still ambiguous. Do not add badges, icons, or custom color unless the native hierarchy proves insufficient.

## 7. Final implementation prompt

```text
Review the live OpenRouter Simple ComfyUI node without redesigning it. Verify controls remain above the two prompt editors; loading, compatible-count, cached, empty, and catalog-error model states are legible; and cable changes never silently select a paid model. Test keyboard focus after each cable transition and inspect dark-mode contrast at a narrow node width. Change only defects observed in the live render, keep native ComfyUI widgets, and rerun ./scripts/verify full.
```
