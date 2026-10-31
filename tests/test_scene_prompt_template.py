import unittest

from nodes.scene_templates import (
    FIELD_DEFAULTS, NEGATIVE_TEMPLATE, PLACEHOLDER, POSITIVE_TEMPLATE,
    DetailedTemplateRenderer as ScenePromptTemplate, render_template,
)


class ScenePromptTemplateTests(unittest.TestCase):
    def test_defaults_produce_complete_sections_and_mapping(self):
        positive, negative, diagnostics = ScenePromptTemplate().build()
        for prompt in (positive, negative):
            self.assertNotIn("{{", prompt)
            self.assertEqual([prompt.count(f"[{section}]") for section in
                              ("COMMON", "SCENE", "CHARACTER")], [1, 1, 1])
        for slot, number in zip("ABC", (2, 3, 4)):
            self.assertIn(f"CHARACTER {slot} — DESIGN SOURCE: IMAGE {number:02d} ONLY", positive)
        self.assertEqual(diagnostics, "OK")

    def test_every_field_is_a_text_widget_and_used(self):
        inputs = ScenePromptTemplate.INPUT_TYPES()["required"]
        used = set(PLACEHOLDER.findall(POSITIVE_TEMPLATE + NEGATIVE_TEMPLATE))
        self.assertEqual(used, set(FIELD_DEFAULTS))
        for name in FIELD_DEFAULTS:
            self.assertEqual(inputs[name][0], "STRING")
            self.assertTrue(inputs[name][1]["multiline"])
            self.assertFalse(inputs[name][1]["dynamicPrompts"])

    def test_input_is_literal_not_recursive_template_code(self):
        value = "日本語\n{{b_name}} \\1 {red|blue}"
        self.assertEqual(render_template("{{a_name}}", {"a_name": value}), value)

    def test_blank_optional_field_omits_label(self):
        positive, negative, _ = ScenePromptTemplate().build()
        self.assertNotIn("Nearby props:", positive)
        self.assertNotIn("Forbidden props:", negative)

    def test_custom_template_and_connected_text(self):
        positive, negative, _ = ScenePromptTemplate().build(
            positive_template="{{ a_name }}\n{{a_pose}}", negative_template="{{a_failure_modes}}",
            a_name="あかり", a_pose="Sitting on a bench", a_failure_modes="Wrong hair color",
        )
        self.assertEqual(positive, "あかり\nSitting on a bench")
        self.assertEqual(negative, "Wrong hair color")

    def test_invalid_fields_and_count(self):
        with self.assertRaisesRegex(ValueError, "Unknown template variables"):
            ScenePromptTemplate().build(positive_template="{{typo}}")
        for total in ("", "2", "three", "3.5", "-1"):
            with self.assertRaises(ValueError):
                ScenePromptTemplate().build(n_total=total)
        with self.assertRaises(ValueError):
            ScenePromptTemplate().build(a_name=" ")

    def test_diagnostics(self):
        self.assertIn("additional people", ScenePromptTemplate().build(n_total="4")[2])
        self.assertEqual(ScenePromptTemplate().build(
            n_total="4", secondary_character_group_spec="One adult standing at the gate."
        )[2], "OK")
        self.assertIn("placeholder", ScenePromptTemplate().build(a_name="{{NAME}}")[2])


if __name__ == "__main__":
    unittest.main()
