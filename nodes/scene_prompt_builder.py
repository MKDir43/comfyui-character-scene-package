"""JSON presets for Build Scene; TXT loaders remain independent."""

import json
from pathlib import Path

from .multi_reference_loader import load_image, empty_image
from . import scene_templates

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHARACTER_ROOT = ROOT / "examples" / "character-references"
SCENE_ROOT = ROOT / "presets" / "scenes"
CHARACTER_FIELDS = {
    "name", "hair_spec", "eye_color", "facial_marks", "hair_silhouette",
    "age_and_context", "fixed_features", "accessory_specs", "failure_modes",
}
SLOT_FIELDS = {"position", "gaze", "pose", "expression", "unique_details", "nearby_props", "omitted_features"}


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read JSON {path}: {error}") from error
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError(f"{path}: expected an object with schema_version: 1")
    return data


def text_fields(data, allowed, label):
    if not isinstance(data, dict):
        raise ValueError(f"{label}: expected a JSON object")
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"{label}: unknown fields: {', '.join(sorted(unknown))}")
    if any(not isinstance(value, str) for value in data.values()):
        raise ValueError(f"{label}: all field values must be strings")
    return data


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes reference directory: {relative}")
    return path


def selected_templates(slots, templates=scene_templates):
    """Reuse the detailed template blocks verbatim; only vary occupied slots."""
    common, rest = templates.POSITIVE_TEMPLATE.split("\n[SCENE]\n", 1)
    scene, character = rest.split("\n[CHARACTER]\n", 1)
    common = common.replace("A ×1, B ×1, C ×1", ", ".join(f"{s.upper()} ×1" for s in slots))
    mapping_start = common.index("- A =")
    mapping_end = common.index("Each position uses only")
    common = common[:mapping_start] + "\n".join(
        f"- {s.upper()} = {{{{{s}_position}}}} = Image {i:02d} ({{{{{s}_name}}}}) — appears once"
        for i, s in enumerate(slots, 2)
    ) + "\n" + common[mapping_end:]
    # The source has one scene/character block for each of the original A/B/C slots.
    scene_prefix = scene[:scene.index("\nA (")]
    scene_tail = scene[scene.index("\nAll characters in this group:"):]
    old_hair = "A: {{a_hair_silhouette}} / B: {{b_hair_silhouette}} / C: {{c_hair_silhouette}}"
    scene_tail = scene_tail.replace(old_hair, " / ".join(f"{s.upper()}: {{{{{s}_hair_silhouette}}}}" for s in slots))
    scene_blocks = []
    character_blocks = []
    for i, slot in enumerate(slots, 2):
        index = "abc".index(slot)
        start = scene.index(f"\n{slot.upper()} (")
        end = scene.index(f"\n{'ABC'[index + 1]} (") if index < 2 else scene.index("\nAll characters in this group:")
        scene_blocks.append(scene[start:end])
        start = character.index(f"\nCHARACTER {slot.upper()} —")
        end = character.index(f"\nCHARACTER {'ABC'[index + 1]} —") if index < 2 else character.index("\n{{extra_character_positive}}")
        block = character[start:end].replace(f"IMAGE {index + 2:02d} ONLY", f"IMAGE {i:02d} ONLY")
        character_blocks.append(block)
    positive = common + "\n[SCENE]\n" + scene_prefix + "".join(scene_blocks) + scene_tail
    positive += "\n[CHARACTER]\n" + "".join(character_blocks) + "\n{{extra_character_positive}}"
    negative = templates.NEGATIVE_TEMPLATE[:templates.NEGATIVE_TEMPLATE.index("\nA — IMAGE 02:")]
    negative += "\n" + "\n".join(f"{s.upper()} — IMAGE {i:02d}: {{{{{s}_failure_modes}}}}" for i, s in enumerate(slots, 2))
    negative += "\n{{extra_character_negative}}\n"
    return positive, negative


class ScenePromptTemplate:
    TEMPLATE_MODULE = scene_templates

    @classmethod
    def INPUT_TYPES(cls):
        scenes = sorted(p.name for p in SCENE_ROOT.glob("*.json")) or ["None"]
        return {"required": {
            "scene": (scenes,),
            **{f"character_{slot}": ("STRING", {"default": "None", "multiline": False,
                 "tooltip": "Folder name under character_root containing character.json. Empty or None disables this slot."}) for slot in "abc"},
            "scene_overrides": ("STRING", {"default": "{}", "multiline": True, "dynamicPrompts": False}),
        }, "optional": {
            "character_root": ("STRING", {"default": "", "multiline": False,
                "tooltip": f"Character reference directory on the ComfyUI server. Empty uses {DEFAULT_CHARACTER_ROOT}"}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE", "IMAGE", "IMAGE", "INT", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "diagnostics", "image_02", "image_03", "image_04", "character_count", "character_mapping")
    FUNCTION = "build"
    CATEGORY = "ComfyUI Character Scene Package/Prompts"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def build(self, scene, character_a="None", character_b="None", character_c="None", scene_overrides="{}", character_root=""):
        reference_root = Path(character_root.strip()).expanduser().resolve() if character_root.strip() else DEFAULT_CHARACTER_ROOT.resolve()
        if not reference_root.is_dir():
            raise ValueError(f"Character reference directory does not exist: {reference_root}")
        scene_data = read_json(inside(SCENE_ROOT, scene))
        if set(scene_data) - {"schema_version", "name", "values", "slots"}:
            raise ValueError("Scene JSON: use schema_version, name, values and slots only")
        try:
            override = json.loads(scene_overrides)
        except ValueError as error:
            raise ValueError(f"scene_overrides: invalid JSON: {error}") from error
        if not isinstance(override, dict) or set(override) - {"values", "slots"}:
            raise ValueError("scene_overrides accepts only values and slots objects")
        templates = self.TEMPLATE_MODULE
        values = dict(templates.FIELD_DEFAULTS)
        global_fields = {key for key in values if not key.startswith(("a_", "b_", "c_"))}
        for source in (scene_data, override):
            values.update(text_fields(source.get("values", {}), global_fields, "scene.values"))
        selections = {s: name.strip() for s, name in zip("abc", (character_a, character_b, character_c))
                      if name.strip() and name.strip().lower() != "none"}
        if not selections:
            raise ValueError("Select at least one character JSON in character_a/b/c")
        if len(set(selections.values())) != len(selections):
            raise ValueError("Select a different character for each occupied slot")
        scene_slots = {}
        for source in (scene_data, override):
            slots = source.get("slots", {})
            if not isinstance(slots, dict) or set(slots) - set("abc"):
                raise ValueError("scene.slots accepts only a, b and c objects")
            for slot, fields in slots.items():
                scene_slots.setdefault(slot, {}).update(text_fields(fields, SLOT_FIELDS, f"slots.{slot}"))
        images, mapping, warnings = [], [], []
        for number, (slot, selection) in enumerate(selections.items(), 2):
            folder = inside(reference_root, selection)
            data = read_json(folder / "character.json")
            if set(data) - {"schema_version", "image", "fields"}:
                raise ValueError(f"{selection}: use schema_version, image and fields only")
            fields = text_fields(data.get("fields", {}), CHARACTER_FIELDS, f"{selection}.fields")
            for required in ("name", "hair_spec", "eye_color", "fixed_features"):
                if not fields.get(required, "").strip():
                    raise ValueError(f"{selection}: missing fields.{required}")
            for key, value in fields.items():
                if key != "eye_color":
                    values[f"{slot}_{key}"] = value
            slot_values = scene_slots.get(slot, {})
            for key, value in slot_values.items():
                if key != "gaze":
                    values[f"{slot}_{key}"] = value
            if not values[f"{slot}_position"].strip():
                raise ValueError(f"slots.{slot}.position must not be empty")
            gaze = slot_values.get("gaze", "gaze as drawn in Image 01")
            values[f"{slot}_eyes_and_gaze"] = fields["eye_color"] + "; " + gaze
            image_name = data.get("image")
            if not isinstance(image_name, str) or not image_name.strip():
                raise ValueError(f"{selection}: image must be a relative filename")
            images.append(load_image(inside(folder, image_name)))
            mapping.append(f"Character {slot.upper()} = Image {number:02d} = {fields['name']} ({selection})")
        explicit = {**scene_data.get("values", {}), **override.get("values", {})}
        if "n_total" not in explicit:
            values["n_total"] = str(len(selections))
        if "category_breakdown" not in explicit:
            values["category_breakdown"] = "assigned characters " + ", ".join(s.upper() for s in selections)
        if not values["n_total"].isdigit() or int(values["n_total"]) < len(selections):
            raise ValueError("n_total must be an integer at least equal to the selected character count")
        if int(values["n_total"]) > len(selections) and not values["secondary_character_group_spec"].strip():
            warnings.append("Describe additional people in secondary_character_group_spec.")
        positive_template, negative_template = selected_templates(selections, templates)
        positive = templates.render_template(positive_template, values)
        negative = templates.render_template(negative_template, values)
        if "{{" in positive + negative or "}}" in positive + negative:
            warnings.append("Unresolved placeholder-like text remains in the supplied values.")
        while len(images) < 3:
            images.append(empty_image())
        return positive, negative, "\n".join(warnings) or "OK", *images, len(selections), "\n".join(mapping)
