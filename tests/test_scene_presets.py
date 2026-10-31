import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from nodes import scene_prompt_builder as builder
from nodes.scene_prompt_builder_nsfw import ScenePromptTemplateNSFW
from nodes import scene_templates_nsfw
from nodes.scene_templates import FIELD_DEFAULTS, POSITIVE_TEMPLATE, NEGATIVE_TEMPLATE, render_template


class ScenePresetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.characters = self.root / "characters"
        self.scenes = self.root / "scenes"
        self.scenes.mkdir()
        self.write(self.scenes / "test.json", {
            "schema_version": 1, "values": {},
            "slots": {"a": {"position": "right", "pose": "Standing at the gate", "gaze": "looking left"}},
        })
        for name, color in (("red", "red"), ("blue", "blue"), ("green", "green")):
            folder = self.characters / name
            folder.mkdir(parents=True)
            Image.new("RGB", (2, 3), color).save(folder / "character.png")
            self.write(folder / "character.json", {
                "schema_version": 1, "image": "character.png",
                "fields": {"name": name, "hair_spec": name + " hair", "eye_color": name + " eyes",
                           "fixed_features": name + " features", "failure_modes": "wrong " + name},
            })
            (folder / "positive.txt").write_text("TXT MUST NOT BE READ", encoding="utf-8")
        for name, value in (("DEFAULT_CHARACTER_ROOT", self.characters), ("SCENE_ROOT", self.scenes)):
            patcher = patch.object(builder, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_three_slot_template_keeps_original_text(self):
        positive, negative = builder.selected_templates("abc")
        self.assertEqual(render_template(positive, FIELD_DEFAULTS), render_template(POSITIVE_TEMPLATE, FIELD_DEFAULTS))
        self.assertEqual(render_template(negative, FIELD_DEFAULTS), render_template(NEGATIVE_TEMPLATE, FIELD_DEFAULTS))

    def test_character_swap_preserves_scene_and_updates_image_and_text(self):
        red = builder.ScenePromptTemplate().build("test.json", character_a="red")
        blue = builder.ScenePromptTemplate().build("test.json", character_a="blue")
        for result in (red, blue):
            self.assertIn("Standing at the gate", result[0])
            self.assertIn("looking left", result[0])
            self.assertIn("[COMMON]", result[0])
            self.assertIn("[SCENE]", result[0])
            self.assertIn("[CHARACTER]", result[0])
            self.assertNotIn("TXT MUST NOT BE READ", result[0])
            self.assertNotIn("CHARACTER B", result[0])
            self.assertNotIn("{{", result[0])
            self.assertEqual(result[6], 1)
        self.assertIn("red hair", red[0])
        self.assertNotIn("red hair", blue[0])
        self.assertEqual(red[3].shape, (1, 3, 2, 3))
        self.assertEqual(red[3][0, 0, 0].tolist(), [1, 0, 0])
        self.assertEqual(blue[3][0, 0, 0].tolist(), [0, 0, 1])
        self.assertEqual(red[4].shape, (1, 1, 1, 3))

    def test_unused_middle_slot_keeps_position_identity(self):
        result = builder.ScenePromptTemplate().build("test.json", character_a="red", character_c="green")
        self.assertIn("CHARACTER C — DESIGN SOURCE: IMAGE 03 ONLY", result[0])
        self.assertIn("C = back-left, furthest = Image 03", result[0])
        self.assertNotIn("CHARACTER B", result[0])
        self.assertEqual(result[6], 2)

    def test_overrides_are_scene_only_and_preserve_newlines(self):
        result = builder.ScenePromptTemplate().build("test.json", character_a="red", scene_overrides=json.dumps({
            "values": {"lighting": "Warm light\nSoft shadows"}, "slots": {"a": {"pose": "Sitting"}},
        }))
        self.assertIn("Warm light\nSoft shadows", result[0])
        self.assertIn("Pose: Sitting", result[0])
        with self.assertRaises(ValueError):
            builder.ScenePromptTemplate().build("test.json", character_a="red", scene_overrides='{"slots":{"a":{"name":"wrong"}}}')

    def test_invalid_selections_and_schema(self):
        node = builder.ScenePromptTemplate()
        with self.assertRaises(ValueError):
            node.build("test.json")
        with self.assertRaises(ValueError):
            node.build("test.json", character_a="red", character_b="red")
        with self.assertRaises(ValueError):
            node.build("../escape.json", character_a="red")
        self.write(self.characters / "red" / "character.json", {"schema_version": 99})
        with self.assertRaises(ValueError):
            node.build("test.json", character_a="red")

    def test_file_changes_are_reloaded_and_choices_use_json(self):
        schema = builder.ScenePromptTemplate.INPUT_TYPES()["required"]
        self.assertEqual(len(schema), 5)
        self.assertEqual(schema["character_a"][0], "STRING")
        path = self.characters / "red" / "character.json"
        data = json.loads(path.read_text())
        data["fields"]["hair_spec"] = "changed hairstyle"
        self.write(path, data)
        self.assertIn("changed hairstyle", builder.ScenePromptTemplate().build("test.json", character_a="red")[0])

    def test_nsfw_initial_output_matches_original(self):
        for selections in ({"character_a": "red"}, {"character_a": "red", "character_c": "blue"},
                           {"character_a": "red", "character_b": "blue", "character_c": "green"}):
            original = builder.ScenePromptTemplate().build("test.json", **selections)
            nsfw = ScenePromptTemplateNSFW().build("test.json", **selections)
            self.assertEqual(original[:3], nsfw[:3])
            self.assertEqual(original[6:], nsfw[6:])
            for index in (3, 4, 5):
                self.assertTrue(original[index].equal(nsfw[index]))

    def test_nsfw_uses_its_own_defaults_templates_and_renderer(self):
        baseline = builder.ScenePromptTemplate().build("test.json", character_a="red")
        positive = scene_templates_nsfw.POSITIVE_TEMPLATE.replace(
            "[COMMON]", "[COMMON]\nNSFW positive: {{custom_instruction}}", 1)
        negative = scene_templates_nsfw.NEGATIVE_TEMPLATE.replace(
            "[COMMON]", "[COMMON]\nNSFW negative", 1)
        with patch.dict(scene_templates_nsfw.FIELD_DEFAULTS, {
            "medium_and_finish": "Clean vector illustration", "custom_instruction": "Default instruction",
        }), patch.object(scene_templates_nsfw, "POSITIVE_TEMPLATE", positive), \
                patch.object(scene_templates_nsfw, "NEGATIVE_TEMPLATE", negative), \
                patch.object(scene_templates_nsfw, "render_template", wraps=scene_templates_nsfw.render_template) as renderer:
            result = ScenePromptTemplateNSFW().build(
                "test.json", character_a="red",
                scene_overrides='{"values":{"custom_instruction":"Only this variant"}}',
            )
            self.assertIn("Clean vector illustration", result[0])
            self.assertIn("NSFW positive: Only this variant", result[0])
            self.assertIn("NSFW negative", result[1])
            self.assertEqual(renderer.call_count, 2)
            unchanged = builder.ScenePromptTemplate().build("test.json", character_a="red")
            self.assertEqual(baseline[:3], unchanged[:3])
            with self.assertRaisesRegex(ValueError, "unknown fields"):
                builder.ScenePromptTemplate().build(
                    "test.json", character_a="red", scene_overrides='{"values":{"custom_instruction":"unsupported"}}')

    def test_custom_root_and_empty_slots(self):
        other = self.root / "custom references"
        self.characters.rename(other)
        result = builder.ScenePromptTemplate().build(
            "test.json", character_a=" red ", character_b="", character_c="none",
            character_root=str(other),
        )
        self.assertIn("red hair", result[0])
        self.assertEqual(result[6], 1)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            builder.ScenePromptTemplate().build("test.json", character_a="red", character_root=str(other / "missing"))
        with self.assertRaisesRegex(ValueError, "escapes"):
            builder.ScenePromptTemplate().build("test.json", character_a="../outside", character_root=str(other))


if __name__ == "__main__":
    unittest.main()
