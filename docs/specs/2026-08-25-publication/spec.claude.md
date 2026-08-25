# Publish OpenRouter Simple publicly

- **Work type:** `feature/app`
- **Status:** `draft` — proceed under explicit repository-creation and publication authority
- **Review surface:** [`spec.human.md`](./spec.human.md)

## 1. Problem / Context

The complete custom node exists only as a local Git repository and a manually deployed RunPod copy. The user requested a new public `Hearmeman24` repository and initial Comfy Registry publication using the publishing key stored in 1Password.

## 2. Approach & Why

- Preserve the existing Registry node ID `comfyui-openrouter-simple` and semantic version `0.1.0`; both are already authoritative project metadata. — evidence: `pyproject.toml:1-5`
- Preserve publisher `hearmeman24`, which is already declared in the package and has been independently confirmed active through the public Registry API. — evidence: `pyproject.toml:13-16`
- Add the required repository URL and documented ComfyUI minimum before packing. The README currently states the minimum but the package metadata does not. — evidence: `README.md:22-30`, `pyproject.toml:1-16`
- Replace the placeholder clone URL and the obsolete statement that the project has no remote or Registry publication. — evidence: `README.md:26-30`, `README.md:107-116`

## 3. Acceptance Criteria

- [ ] A new public repository exists at `https://github.com/Hearmeman24/ComfyUI-OpenRouter-Simple` with `main` at the tested release commit. → (ask: "Create a new public Hearmeman24 repository, push the node there")
- [ ] Version `0.1.0` is publicly listed and installable from the Comfy Registry under publisher `hearmeman24`. → (ask: "push it to comfy ui registry as well")
- [ ] The publication token is obtained from the existing 1Password item without appearing in repository content or command output. → (ask: "key is in 1pass")

## 4. Scope & Non-Goals

**In scope:** publication metadata, README installation links, historical spec, a release commit/tag, GitHub repository creation/push, one Registry CLI publication, and public verification.

**Non-goals:** GitHub Actions automation, GitHub repository secrets, icons/banners, new node behavior, another paid OpenRouter request, or RunPod changes.

## 5. Key Decisions & Constraints

- **Decided:** Keep Registry ID `comfyui-openrouter-simple` because the project already declares it and first publication makes the ID immutable. — evidence: `pyproject.toml:1-4`
- **Decided:** Publish version `0.1.0` as the initial release. — evidence: `pyproject.toml:4`
- **Constraint:** The package must retain its MIT license and runtime dependencies. — evidence: `pyproject.toml:5-11`, `LICENSE:1-20`
- **Constraint:** Only text outputs and environment-based API-key handling remain documented; publication must not alter runtime behavior. — evidence: `README.md:20-40`
- **Scale:** Public Registry distribution means arbitrary user installs; deterministic Git-tracked packaging and explicit system requirements are the relevant bottlenecks.

## 6. Code Surface Map

- `pyproject.toml:1-16` — Registry identity, version, dependencies, and publisher metadata.
- `README.md:22-40` — Git/Registry installation and API-key setup.
- `README.md:96-116` — verification and operational boundary.
- `LICENSE:1-20` — public distribution license.
- `scripts/verify` — repository verification interface.

## 7. Ultracode Dispatch Notes

**Build first (sequential):** Complete and validate package metadata.

**External publication sequence (serialized):**

- **Repository** — create public GitHub repository and push the green commit to `main`. Writes external GitHub repository state.
- **Registry** — retrieve the token from 1Password and publish only after the repository is public. Writes immutable Registry version `0.1.0`.
- **Verification** — inspect GitHub visibility/default branch and Registry API/install resolution. Read-only.

**⛓ Collision audit:** Metadata must be frozen before either external write. Registry publication depends on the public repository URL, so the external writes cannot run in parallel.

```yaml
dispatch:
  frozen: [node.py, openrouter_simple, web, tests]
  slices:
    - {key: metadata, writes: [pyproject.toml, README.md, docs/specs/2026-08-25-publication]}
    - {key: github, writes: [external:Hearmeman24/ComfyUI-OpenRouter-Simple]}
    - {key: registry, writes: [external:hearmeman24/comfyui-openrouter-simple/0.1.0]}
  testRunner: "./scripts/verify full && comfy node validate && comfy node pack"
```

## 8. Assumptions & Open Questions

None. GitHub authentication, publisher existence, CLI availability, and the 1Password item have been verified before drafting.
