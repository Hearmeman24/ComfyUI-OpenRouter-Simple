import asyncio
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

from openrouter_simple.cancellation import NodeDeadline
from openrouter_simple.client import ChatResult
from openrouter_simple.media import PreparedMedia
from openrouter_simple.models import ModelInfo, ModelSnapshot


class NodeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "comfyui_openrouter_simple",
            root / "__init__.py",
            submodule_search_locations=[str(root)],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cls.module = module
        cls.node_module = sys.modules[f"{spec.name}.node"]

    def test_registration_and_text_only_outputs(self):
        node = self.module.NODE_CLASS_MAPPINGS["OpenRouterSimple"]
        self.assertEqual(node.RETURN_TYPES, ("STRING", "STRING", "STRING"))
        self.assertEqual(node.RETURN_NAMES, ("text", "info", "credits"))
        self.assertEqual(self.module.WEB_DIRECTORY, "./web")

    def test_exact_approved_input_surface(self):
        node = self.module.NODE_CLASS_MAPPINGS["OpenRouterSimple"]
        inputs = node.INPUT_TYPES()
        self.assertEqual(
            set(inputs["required"]),
            {
                "system_prompt",
                "user_prompt",
                "model",
                "reasoning_effort",
                "timeout_seconds",
                "temperature",
                "max_tokens",
                "response_format",
                "zdr",
            },
        )
        self.assertEqual(
            list(inputs["optional"]),
            [
                "image",
                "image_2",
                "image_3",
                "video",
                "video_2",
                "video_3",
                "audio",
                "audio_2",
                "audio_3",
            ],
        )

    def test_all_populated_media_slots_are_prepared_in_stable_order(self):
        values = [(name, object()) for name in (
            "image",
            "image_2",
            "image_3",
            "video",
            "video_2",
            "video_3",
            "audio",
            "audio_2",
            "audio_3",
        )]

        async def prepare(modality):
            return PreparedMedia(modality, "application/octet-stream", modality.encode(), 1, {})

        async def prepare_image_mock(_deadline, _value):
            return await prepare("image")

        async def prepare_video_mock(_deadline, _value):
            return await prepare("video")

        async def prepare_audio_mock(_deadline, _value):
            return await prepare("audio")

        with (
            mock.patch.object(
                self.node_module,
                "prepare_image",
                side_effect=prepare_image_mock,
            ),
            mock.patch.object(
                self.node_module,
                "prepare_video",
                side_effect=prepare_video_mock,
            ),
            mock.patch.object(
                self.node_module,
                "prepare_audio",
                side_effect=prepare_audio_mock,
            ),
        ):
            prepared = asyncio.run(
                self.node_module._prepare_media(NodeDeadline(2), media_inputs=values)
            )

        self.assertEqual([name for name, _item in prepared], [name for name, _value in values])
        self.assertEqual(
            [item.modality for _name, item in prepared],
            ["image"] * 3 + ["video"] * 3 + ["audio"] * 3,
        )

    def test_sparse_additional_slots_reach_payload_and_named_info(self):
        selected = ModelInfo(
            id="vendor/omni",
            name="Omni",
            input_modalities=("text", "image", "video", "audio"),
            output_modalities=("text",),
            supported_parameters=("max_tokens",),
            reasoning=False,
        )
        snapshot = ModelSnapshot(models=(selected,), fetched_at=1.0)
        captured_payload = None

        async def catalog_get(**_kwargs):
            return snapshot

        async def prepare_image_mock(_deadline, value):
            return PreparedMedia("image", "image/webp", str(value).encode(), 1, {})

        async def prepare_video_mock(_deadline, value):
            return PreparedMedia("video", "video/mp4", str(value).encode(), 1, {})

        async def prepare_audio_mock(_deadline, value):
            return PreparedMedia("audio", "audio/mpeg", str(value).encode(), 1, {})

        async def create_chat_mock(_deadline, payload, _api_key):
            nonlocal captured_payload
            captured_payload = payload
            return ChatResult(text="ok", response_id="gen-test", usage={})

        async def credits_mock(_deadline, _api_key):
            return "credits"

        with (
            mock.patch.object(self.node_module.CATALOG, "get", side_effect=catalog_get),
            mock.patch.object(self.node_module, "resolve_generation_key", return_value="key"),
            mock.patch.object(self.node_module, "prepare_image", side_effect=prepare_image_mock),
            mock.patch.object(self.node_module, "prepare_video", side_effect=prepare_video_mock),
            mock.patch.object(self.node_module, "prepare_audio", side_effect=prepare_audio_mock),
            mock.patch.object(self.node_module, "create_chat", side_effect=create_chat_mock),
            mock.patch.object(self.node_module, "lookup_credits", side_effect=credits_mock),
        ):
            text, info_json, credits = asyncio.run(
                self.node_module.OpenRouterSimple().run(
                    system_prompt="",
                    user_prompt="enumerate",
                    model="vendor/omni",
                    reasoning_effort="auto",
                    timeout_seconds=5,
                    temperature=1,
                    max_tokens=64,
                    response_format="text",
                    zdr=False,
                    image="first-image",
                    image_3="third-image",
                    video_2="second-video",
                    audio_3={"clip": "third-audio"},
                )
            )

        self.assertEqual((text, credits), ("ok", "credits"))
        self.assertIsNotNone(captured_payload)
        content = captured_payload["messages"][0]["content"]
        self.assertEqual(
            [part["type"] for part in content],
            ["text", "image_url", "image_url", "video_url", "input_audio"],
        )
        info = json.loads(info_json)
        self.assertEqual(info["required_modalities"], ["audio", "image", "text", "video"])
        self.assertEqual(list(info["media"]), ["image", "image_3", "video_2", "audio_3"])


if __name__ == "__main__":
    unittest.main()
