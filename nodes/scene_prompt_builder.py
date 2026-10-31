"""JSON presets for Build Scene; TXT loaders remain independent."""

import json
from pathlib import Path

from .multi_reference_loader import load_image, empty_image
from . import scene_templates
from .template_sections import split_marker

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHARACTER_ROOT = ROOT / "examples" / "character-references"
SCENE_ROOT = ROOT / "presets" / "scenes"
CHARACTER_FIELDS = {
    "name", "hair_spec", "eye_color", "facial_marks", "hair_silhouette",
    "age_and_context", "fixed_features", "accessory_specs", "failure_modes",
}
SLOT_FIELDS = CHARACTER_FIELDS | {"position", "gaze", "eyes_and_gaze", "pose", "expression", "unique_details", "nearby_props", "omitted_features"}


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


def input_path(selection, root, label):
    """Explicit root means relative input; no root means an absolute input."""
    path = Path(selection.strip()).expanduser()
    if root.strip():
        if path.is_absolute() or path.drive:
            raise ValueError(f"{label}: use a relative path when root is specified")
        return inside(Path(root.strip()).expanduser().resolve(), selection.strip())
    if not path.is_absolute():
        raise ValueError(f"{label}: use an absolute path when root is empty")
    return path.resolve()


def find_scene(root, selection):
    """Resolve a relative path or find a unique JSON filename recursively."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Scene JSON directory does not exist: {root}")
    selection = selection.strip().replace("\\", "/")
    if not selection or Path(selection).suffix.lower() != ".json":
        raise ValueError("scene must be a JSON filename or relative path under json_root")
    direct = inside(root, selection)
    if "/" in selection:
        if not direct.is_file():
            raise ValueError(f"Scene JSON not found: {direct}")
        return direct
    candidates = sorted(
        path for path in root.rglob("*.json")
        if path.is_file() and path.resolve().is_relative_to(root)
    )
    matches = [path for path in candidates if path.name.casefold() == selection.casefold()]
    if len(matches) == 1:
        return matches[0].resolve()
    if len(matches) > 1:
        options = ", ".join(path.relative_to(root).as_posix() for path in matches)
        raise ValueError(f"Multiple scene JSON files named {selection}. Use a relative path: {options}")
    options = ", ".join(path.relative_to(root).as_posix() for path in candidates[:20]) or "(none)"
    raise ValueError(f"Scene JSON not found: {selection} under {root}. Available JSON files (up to 20): {options}")


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
    scene_prefix, remaining = split_marker(scene, "SCENE_SLOT_A")
    scene_parts = {}
    scene_parts["a"], remaining = split_marker(remaining, "SCENE_SLOT_B")
    scene_parts["b"], remaining = split_marker(remaining, "SCENE_SLOT_C")
    scene_parts["c"], scene_tail = split_marker(remaining, "GROUP_RULES_START")
    character_prefix, remaining = split_marker(character, "CHARACTER_SLOT_A")
    character_parts = {}
    character_parts["a"], remaining = split_marker(remaining, "CHARACTER_SLOT_B")
    character_parts["b"], remaining = split_marker(remaining, "CHARACTER_SLOT_C")
    character_parts["c"], character_tail = split_marker(remaining, "CHARACTER_EXTRA_START")
    old_hair = "A: {{a_hair_silhouette}} / B: {{b_hair_silhouette}} / C: {{c_hair_silhouette}}"
    scene_tail = scene_tail.replace(old_hair, " / ".join(f"{s.upper()}: {{{{{s}_hair_silhouette}}}}" for s in slots))
    scene_blocks = []
    character_blocks = []
    for i, slot in enumerate(slots, 2):
        index = "abc".index(slot)
        scene_blocks.append(scene_parts[slot])
        block = character_parts[slot].replace(f"IMAGE {index + 2:02d} ONLY", f"IMAGE {i:02d} ONLY")
        character_blocks.append(block)
    positive = common + "\n[SCENE]\n" + scene_prefix + "".join(scene_blocks) + scene_tail
    positive += "\n[CHARACTER]\n" + character_prefix + "".join(character_blocks) + character_tail
    negative = templates.NEGATIVE_TEMPLATE[:templates.NEGATIVE_TEMPLATE.index("\nA — IMAGE 02:")]
    negative += "\n" + "\n".join(f"{s.upper()} — IMAGE {i:02d}: {{{{{s}_failure_modes}}}}" for i, s in enumerate(slots, 2))
    negative += "\n{{extra_character_negative}}\n"
    return positive, negative


class ScenePromptTemplate:
    TEMPLATE_MODULE = scene_templates

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "scene": ("STRING", {"default": "", "multiline": False,
                "tooltip": "Scene JSON absolute path, or relative path when json_root is set."}),
            **{f"character_{slot}": ("STRING", {"default": "None", "multiline": False,
                 "tooltip": "Character folder absolute path, or relative path when character_root is set. Empty or None disables this slot."}) for slot in "abc"},
            "scene_overrides": ("STRING", {"default": "{}", "multiline": True, "dynamicPrompts": False}),
        }, "optional": {
            "character_root": ("STRING", {"default": "", "multiline": False,
                "tooltip": "Optional base directory for relative character folder paths. Empty requires absolute paths."}),
            "json_root": ("STRING", {"default": "", "multiline": False,
                "tooltip": "Optional base directory for relative scene JSON paths. Empty requires an absolute scene path."}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE", "IMAGE", "IMAGE", "INT", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "diagnostics", "image_02", "image_03", "image_04", "character_count", "character_mapping")
    FUNCTION = "build"
    CATEGORY = "ComfyUI Character Scene Package/Prompts"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def build(self, scene, character_a="None", character_b="None", character_c="None", scene_overrides="{}", character_root="", json_root=""):
        scene_path = input_path(scene, json_root, "scene")
        if json_root.strip():
            scene_path = find_scene(Path(json_root.strip()).expanduser(), scene)
        scene_data = read_json(scene_path)
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
            folder = input_path(selection, character_root, f"character_{slot}")
            if not folder.is_dir():
                raise ValueError(f"Character directory does not exist: {folder}")
            data = read_json(folder / "character.json")
            if set(data) - {"schema_version", "image", "fields"}:
                raise ValueError(f"{selection}: use schema_version, image and fields only")
            fields = text_fields(data.get("fields", {}), CHARACTER_FIELDS, f"{selection}.fields")
            slot_values = scene_slots.get(slot, {})
            fields = {**fields, **{key: value for key, value in slot_values.items() if key in CHARACTER_FIELDS}}
            for required in ("name", "hair_spec", "eye_color", "fixed_features"):
                if not fields.get(required, "").strip():
                    raise ValueError(f"{selection}: missing fields.{required}")
            for key, value in fields.items():
                if key != "eye_color":
                    values[f"{slot}_{key}"] = value
            for key, value in slot_values.items():
                if key not in {"gaze", "eye_color"}:
                    values[f"{slot}_{key}"] = value
            if not values[f"{slot}_position"].strip():
                raise ValueError(f"slots.{slot}.position must not be empty")
            gaze = slot_values.get("gaze", "gaze as drawn in Image 01")
            values[f"{slot}_eyes_and_gaze"] = slot_values.get("eyes_and_gaze", fields["eye_color"] + "; " + gaze)
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
