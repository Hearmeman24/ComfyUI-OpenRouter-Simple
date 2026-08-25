# Publish OpenRouter Simple publicly

**Type:** `feature/app` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

`Hearmeman24/ComfyUI-OpenRouter-Simple` is a public GitHub repository with `main` at the tested release commit, and version `0.1.0` is publicly installable from the Comfy Registry as `comfyui-openrouter-simple`.

## 🪤 Gotchas

- The Registry node ID becomes immutable after first publication, so this release preserves the existing `comfyui-openrouter-simple` project name.
- The registry archive is built from Git-tracked files. Publishing must happen only after the metadata commit is pushed and validation/packing pass.
- The Registry token must come from 1Password and must never be printed, committed, or placed in shell history as a literal.

## Done when

- [ ] The GitHub repository exists under `Hearmeman24`, is public, and exposes `main` at the release commit.
- [ ] The repository README contains working GitHub and Registry installation instructions.
- [ ] `comfy node validate`, package inspection, and the full project verification suite pass.
- [ ] Registry version `0.1.0` is published under publisher `hearmeman24` and its public API/listing confirms the version.
- [ ] A fresh Registry install resolves the published package metadata.

## The plan

1. Complete `pyproject.toml` and README publication metadata.
2. Validate, pack, inspect, and commit the release surface.
3. Create the public GitHub repository and push the release commit to `main`.
4. Read the token from 1Password, publish `0.1.0`, then verify the public Registry record and installation path.

## ✂️ Not asked for — cut

- Automated GitHub Actions publishing and a copied Registry token in GitHub Secrets are excluded; this request is for the initial publication, and 1Password remains the secret owner.

