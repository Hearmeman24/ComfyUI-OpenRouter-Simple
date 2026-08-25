import importlib.util
import sys
import unittest
from pathlib import Path


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
                "seed",
                "timeout_seconds",
                "temperature",
                "max_tokens",
                "response_format",
                "zdr",
            },
        )
        self.assertEqual(set(inputs["optional"]), {"image", "video", "audio"})


if __name__ == "__main__":
    unittest.main()
