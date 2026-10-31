"""Check ComfyUI's package entry point without installing image dependencies."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class RegistrationTests(unittest.TestCase):
    def test_entry_point_preserves_workflow_contracts(self):
        package_name = "_character_scene_tools_registration_test"
        spec = importlib.util.spec_from_file_location(
            package_name, ROOT / "__init__.py",
            submodule_search_locations=[str(ROOT)],
        )
        module = importlib.util.module_from_spec(spec)
        torch = types.ModuleType("torch")
        torch.Tensor = type("Tensor", (), {})
        pil = types.ModuleType("PIL")
        pil.Image = types.ModuleType("PIL.Image")
        pil.ImageOps = types.ModuleType("PIL.ImageOps")
        with patch.dict(sys.modules, {
            package_name: module,
            "numpy": types.ModuleType("numpy"),
            "torch": torch,
            "PIL": pil,
        }):
            spec.loader.exec_module(module)
            registry = module.NODE_CLASS_MAPPINGS
            self.assertEqual(set(registry), {
                "ImagePromptPackageLoader", "MultiPromptPackageLoader", "ScenePromptTemplate",
                "ScenePromptTemplateNSFW",
            })
            self.assertEqual(set(registry), set(module.NODE_DISPLAY_NAME_MAPPINGS))
            self.assertEqual(len(set(module.NODE_DISPLAY_NAME_MAPPINGS.values())), 4)
            single = registry["ImagePromptPackageLoader"]
            self.assertEqual(list(single.INPUT_TYPES()["required"]), ["root_path", "package_name"])
            self.assertEqual(single.RETURN_NAMES, ("image", "positive_prompt", "negative_prompt"))
            self.assertEqual(single.RETURN_TYPES, ("IMAGE", "STRING", "STRING"))
            multi = registry["MultiPromptPackageLoader"]
            self.assertEqual(list(multi.INPUT_TYPES()["required"]),
                             ["root_path"] + [f"package_{i}" for i in range(1, 6)])
            self.assertEqual(multi.RETURN_NAMES, (
                "image_02", "image_03", "image_04", "image_05", "image_06",
                "character_positive", "character_negative", "character_count", "character_mapping",
            ))
            self.assertEqual(multi.RETURN_TYPES, ("IMAGE",) * 5 + ("STRING", "STRING", "INT", "STRING"))
            builder = registry["ScenePromptTemplate"]
            self.assertEqual(builder.RETURN_NAMES, (
                "positive_prompt", "negative_prompt", "diagnostics",
                "image_02", "image_03", "image_04", "character_count", "character_mapping",
            ))
            nsfw = registry["ScenePromptTemplateNSFW"]
            self.assertEqual(builder.INPUT_TYPES(), nsfw.INPUT_TYPES())
            self.assertEqual(builder.RETURN_NAMES, nsfw.RETURN_NAMES)
            self.assertEqual(builder.RETURN_TYPES, nsfw.RETURN_TYPES)
            self.assertIsNot(builder.TEMPLATE_MODULE, nsfw.TEMPLATE_MODULE)
            for cls in registry.values():
                self.assertTrue(cls.CATEGORY.startswith("ComfyUI Character Scene Package/"))
                self.assertTrue(callable(getattr(cls(), cls.FUNCTION)))


if __name__ == "__main__":
    unittest.main()
