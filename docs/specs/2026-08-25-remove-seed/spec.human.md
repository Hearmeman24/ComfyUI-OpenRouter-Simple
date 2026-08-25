# Remove the OpenRouter seed control

**Type:** `bug-fix/recon` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

The OpenRouter node no longer shows or sends a seed. Existing saved nodes load with their remaining widget values in the correct fields, and Google requests cannot fail because ComfyUI generated a seed outside the provider's integer range.

## 🪤 Gotchas

- Old workflows serialize widget values by position. Removing the third widget without migrating that array would shift the old seed into `timeout_seconds` and every later value into the wrong control.
- OpenRouter model metadata may continue to advertise seed support; that must not cause the removed parameter to reappear in payloads or diagnostics.

## Done when

- [ ] No seed widget exists on a newly created node.
- [ ] No request payload or `info.parameters` entry can contain seed.
- [ ] A saved pre-removal widget array drops only its legacy seed value before ComfyUI restores the node.
- [ ] Focused and full verification pass.

## The plan

1. Add contract, payload, and saved-workflow migration regressions.
2. Remove seed from the Python node and payload builder.
3. Migrate legacy positional widget arrays in the existing frontend configure hook.
4. Update documentation, verify, install, and restart local ComfyUI.

