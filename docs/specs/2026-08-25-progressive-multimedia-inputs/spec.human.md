# Progressive media inputs, up to three of each kind

**Type:** `feature/app` · **Full spec:** [`spec.claude.md`](./spec.claude.md)

## ✅ What you'll see when this is done

The node initially shows one image, one video, and one audio socket. Connecting a socket reveals the next socket of that same type, up to three images, three videos, and three audio clips; all connected items are sent as context in one text-output request.

## 🎲 Riding on these assumptions

- **OpenRouter does not publish one universal nine-file guarantee** — its documentation says attachment counts vary by provider and model. The model picker can filter the required modality combination, but a provider may still reject a particular attachment count and the node must show that rejection clearly.

## 🪤 Gotchas

- Existing workflows keep their original `image`, `video`, and `audio` socket names. New sockets are `image_2`, `image_3`, `video_2`, `video_3`, `audio_2`, and `audio_3`.
- Disconnecting a trailing input removes now-unneeded empty sockets, but never removes a socket that still has a link.
- Nine media items may preprocess concurrently under the same total deadline. Any one failure cancels the remaining preparation and prevents the paid POST.
- The live test is direct against OpenRouter, not queued through ComfyUI, and uses temporary derivatives of files in `/Users/avivkaplan/Dump`.

## Done when

- [ ] Each modality autogrows from one visible socket to at most three as preceding sockets are populated.
- [ ] Saved workflows with any valid combination of the nine sockets restore without dropping links.
- [ ] The backend preprocesses and sends every populated socket, including gaps, and reports per-socket media details.
- [ ] Model filtering treats `image_2`/`image_3` as image requirements (and likewise for video/audio), without multiplying modality requirements.
- [ ] Local tests prove all nine content entries, bounded cancellation, and legacy one-of-each compatibility.
- [ ] A bounded direct live request with media derived from `/Users/avivkaplan/Dump` reaches a compatible OpenRouter model; no ComfyUI workflow is submitted.

## The plan

1. Freeze the nine socket names and progressive reveal rule in backend and pure frontend tests.
2. Generalize preprocessing and info output from one item per modality to named media collections.
3. Add the frontend autogrow synchronizer and keep modality-intersection filtering authoritative on both sides.
4. Run the full suite, inspect the real node in ComfyUI, then disclose the exact live request/cost envelope and execute the bounded direct test.

