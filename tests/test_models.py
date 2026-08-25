import unittest

from openrouter_simple.models import normalize_model


class ModelTests(unittest.TestCase):
    def test_normalizes_and_checks_modality_intersection(self):
        model = normalize_model(
            {
                "id": "vendor/omni",
                "name": "Omni",
                "architecture": {
                    "input_modalities": ["text", "image", "video", "audio"],
                    "output_modalities": ["text"],
                },
                "supported_parameters": ["temperature", "seed", "reasoning"],
                "reasoning": {"supported": True},
            }
        )
        self.assertIsNotNone(model)
        self.assertTrue(model.accepts({"text", "image", "video", "audio"}))
        self.assertTrue(model.supports("seed"))
        self.assertTrue(model.reasoning)

    def test_rejects_non_text_output_models(self):
        model = normalize_model(
            {
                "id": "vendor/image-only",
                "architecture": {"input_modalities": ["text"], "output_modalities": ["image"]},
            }
        )
        self.assertIsNone(model)

    def test_requires_every_connected_modality(self):
        model = normalize_model(
            {
                "id": "vendor/vision",
                "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]},
            }
        )
        self.assertTrue(model.accepts({"text", "image"}))
        self.assertFalse(model.accepts({"text", "image", "audio"}))


if __name__ == "__main__":
    unittest.main()
