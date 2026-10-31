"""Text-only, all-ages scene prompt assembly; no third-party dependencies."""

import re


# Each key is both a ComfyUI STRING widget and a {{placeholder}} name.
FIELD_DEFAULTS = {
    "medium_and_finish": "Polished finished 2D anime illustration",
    "linework_shading_color_rules": "Clean linework, cel shading, consistent colors.",
    "crisp_elements": "characters and their clothing",
    "softened_elements": "distant background",
    "excluded_styles": "impressionist or painterly",
    "n_total": "3",
    "category_breakdown": "three fully clothed characters, A, B and C",
    "forbidden_extras": "additional people or bystanders",
    "unique_feature_guard": "",
    "distinguishability_rule": "Keep each character's hair silhouette and coloring distinct.",
    "global_override_name": "CLOTHING",
    "clothing_rule": "All characters wear complete, opaque, age-appropriate everyday outfits and shoes.",
    "allowed_clothing": "complete everyday outfits and shoes",
    "forbidden_clothing_items": "",
    "shared_category_rule": "",
    "secondary_character_group_spec": "",
    "environment_description": "A quiet courtyard with a stone path",
    "lighting": "Soft daylight with consistent shadows",
    "background_treatment": "Slightly blurred distant trees",
    "no_modern_items_list": "",
    "pov_type": "Eye-level viewpoint",
    "pov_alias": "observer viewpoint",
    "angle_and_direction": "Match Image 01 exactly",
    "framing_description": "Preserve the full composition of Image 01",
    "foreground_intrusion": "",
    "shared_body_type_spec": "Preserve each character's age and natural proportions from the assigned reference.",
    "gaze_rule": "in the directions drawn in Image 01",
    "whose_arm": "the corresponding visible character's arm",
    "shared_rule_violations": "",
    "age_proportion_violations": "Age changes, distorted body proportions",
    "forbidden_prop_type": "",
    "camera_violations": "Different viewpoint or perspective from Image 01",
    "gaze_violations": "Gaze inconsistent with Image 01",
    "secondary_character_violations": "",
    "setting_violations": "",
    "extra_common_positive": "",
    "extra_scene_positive": "",
    "extra_character_positive": "",
    "extra_common_negative": "",
    "extra_scene_negative": "",
    "extra_character_negative": "",
}

for slot, position in zip("abc", ("front-right, nearest", "center, mid-distance", "back-left, furthest")):
    for field, default in {
        "name": f"Character {slot.upper()}",
        "position": position,
        "hair_spec": "Preserve the assigned reference's hair color and hairstyle",
        "eyes_and_gaze": "Preserve eye color; gaze as drawn in Image 01",
        "facial_marks": "",
        "pose": "Preserve this figure's exact pose in Image 01",
        "expression": "A relaxed, natural expression",
        "unique_details": "",
        "nearby_props": "",
        "hair_silhouette": "Match the assigned reference",
        "age_and_context": "Preserve the assigned reference's apparent age",
        "fixed_features": "Preserve face, hair, coloring and identifying features",
        "accessory_specs": "",
        "omitted_features": "",
        "failure_modes": "Incorrect face, hair color, hairstyle or identifying features",
    }.items():
        FIELD_DEFAULTS[f"{slot}_{field}"] = default


POSITIVE_TEMPLATE = """[COMMON]
STYLE (authoritative, highest priority): {{medium_and_finish}}.
{{linework_shading_color_rules}}
FOCUS HIERARCHY: {{crisp_elements}} rendered crisply in focus; {{softened_elements}} rendered slightly softer under the same lighting.
NOT {{excluded_styles}}: no visible brushstrokes, texture bleed, sketch lines or hatching.

COUNT & LAYOUT (authoritative): Exactly {{n_total}} people total in frame — {{category_breakdown}}; no more, no fewer. No {{forbidden_extras}}.
Each assigned character appears EXACTLY ONCE: A ×1, B ×1, C ×1; no duplicates, clones or second copies.
{{unique_feature_guard}}
Image 01 is the fixed geometry reference: replace every rough figure one-to-one in place. Preserve camera position, viewing direction, angle, framing, perspective, foreshortening, all positions, poses, depth, overlaps, spacing, ground contact and relative heights exactly as drawn. Do not exchange figures, rearrange the group, change poses, zoom, crop or recompose.

Strict per-position identity mapping (do not swap or blend):
- A = {{a_position}} = Image 02 ({{a_name}}) — appears once
- B = {{b_position}} = Image 03 ({{b_name}}) — appears once
- C = {{c_position}} = Image 04 ({{c_name}}) — appears once
Each position uses only its assigned reference's face, hair and identifying features. Multiple views/panels depict the SAME character: use for design only; never copy their poses, backgrounds or sheet layout.
{{distinguishability_rule}}

{{global_override_name}} OVERRIDE: {{clothing_rule}}
All characters are fully clothed in opaque, age-appropriate clothing in a non-sexual, all-ages scene.
Forbidden clothing/accessories: {{forbidden_clothing_items}}
{{shared_category_rule}}
{{secondary_character_group_spec}}
{{extra_common_positive}}

[SCENE]
Setting: {{environment_description}}.
Lighting: {{lighting}}; background: {{background_treatment}}.
Period restrictions — exclude: {{no_modern_items_list}}
No readable signage or large text.
Camera: {{pov_type}} ({{pov_alias}}), {{angle_and_direction}}; {{framing_description}}.
{{foreground_intrusion}}
"""

for slot in "abc":
    # Substitute slot names only; leave field placeholders for execution time.
    POSITIVE_TEMPLATE += """
SLOT ({{s_position}}): {{s_hair_spec}}; {{s_eyes_and_gaze}}.
Facial marks (left/right relative to the character's own body): {{s_facial_marks}}
Pose: {{s_pose}}.
Expression: {{s_expression}}.
Clothing/accessories per COMMON override.
Unique details and interactions: {{s_unique_details}}
Nearby props: {{s_nearby_props}}
""".replace("SLOT", slot.upper()).replace("{{s_", "{{" + slot + "_")

POSITIVE_TEMPLATE += """
All characters in this group: {{shared_body_type_spec}}
All gaze {{gaze_rule}}.
Each hair silhouette (A: {{a_hair_silhouette}} / B: {{b_hair_silhouette}} / C: {{c_hair_silhouette}}) must read clearly.
{{extra_scene_positive}}

[CHARACTER]
"""

for number, slot in enumerate("abc", 2):
    POSITIVE_TEMPLATE += f"\nCHARACTER {slot.upper()} — DESIGN SOURCE: IMAGE {number:02d} ONLY\n"
    POSITIVE_TEMPLATE += """{{s_name}}, {{s_age_and_context}}.
Preserve face, apparent age and coloring from the reference's main full-body views. Use expression panels for expressions only; ignore vignettes with other people.
Fixed features: {{s_fixed_features}}.
Accessory construction and placement: {{s_accessory_specs}}
Omitted reference features and reasons: {{s_omitted_features}}
Use the scene's clothing override. Omit unspecified reference details. Do not borrow traits from other references.
""".replace("{{s_", "{{" + slot + "_")
POSITIVE_TEMPLATE += "\n{{extra_character_positive}}"

NEGATIVE_TEMPLATE = """[COMMON]
Rough sketch lines, construction lines, hatching, mannequin surfaces, placeholder faces or clothing, unfinished output.
{{excluded_styles}}, visible brushstrokes, painterly texture, overall soft focus (only {{softened_elements}} may be slightly soft).
Extra people beyond exactly {{n_total}}: {{forbidden_extras}}; duplicate characters, clones, mirror copies; swapped or merged identities; transferred hairstyles, hair colors or accessories.
Character-sheet layouts, multiple views of one character, reference panels, captions, annotation text.
Rearranged or exchanged figure positions, changed poses, shifted heads or hands, changed limb directions, altered spacing, overlaps, ground contact or height differences; different camera position, direction, angle, perspective or framing; zoom, cropped figures, recomposed layout.
Malformed anatomy, extra or missing limbs, fused fingers, floating detached hands (every hand must connect to {{whose_arm}}).
Photorealism, 3D rendering, nudity, transparent clothing, sexualized appearance.
{{extra_common_negative}}

[SCENE]
Clothing inconsistent with the allowed outfits: {{allowed_clothing}}.
Forbidden items visible on the body: {{forbidden_clothing_items}}
{{shared_rule_violations}}
{{age_proportion_violations}}
Forbidden props: {{forbidden_prop_type}}
{{camera_violations}}
{{gaze_violations}}
{{secondary_character_violations}}
{{setting_violations}}
Readable text or signage.
{{extra_scene_negative}}

[CHARACTER]
A — IMAGE 02: {{a_failure_modes}}
B — IMAGE 03: {{b_failure_modes}}
C — IMAGE 04: {{c_failure_modes}}
{{extra_character_negative}}
"""

PLACEHOLDER = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")


def render_template(template, values):
    """Omit lines with empty fields. Insert user text literally, in one pass."""
    unknown = set(PLACEHOLDER.findall(template)) - values.keys()
    if unknown:
        raise ValueError("Unknown template variables: " + ", ".join(sorted(unknown)))
    lines = []
    for line in template.splitlines():
        keys = PLACEHOLDER.findall(line)
        if keys and any(not values[key].strip() for key in keys):
            continue
        lines.append(PLACEHOLDER.sub(lambda match: values[match.group(1)].strip(), line))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


class DetailedTemplateRenderer:
    @classmethod
    def INPUT_TYPES(cls):
        fields = {
            "positive_template": POSITIVE_TEMPLATE,
            "negative_template": NEGATIVE_TEMPLATE,
            **FIELD_DEFAULTS,
        }
        return {"required": {
            name: ("STRING", {"default": default, "multiline": True, "dynamicPrompts": False})
            for name, default in fields.items()
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "diagnostics")
    FUNCTION = "build"
    CATEGORY = "Character Scene Tools/Prompts"

    def build(self, positive_template=POSITIVE_TEMPLATE, negative_template=NEGATIVE_TEMPLATE, **kwargs):
        values = {**FIELD_DEFAULTS, **kwargs}
        if any(not isinstance(value, str) for value in values.values()):
            raise ValueError("All template variables must be STRING values.")
        total = values["n_total"].strip()
        if not re.fullmatch(r"[0-9]+", total) or int(total) < 3:
            raise ValueError("n_total must be an integer of at least 3 (fixed slots A/B/C).")
        for slot in "abc":
            for field in ("name", "position"):
                if not values[f"{slot}_{field}"].strip():
                    raise ValueError(f"{slot}_{field} must not be empty.")
        positive = render_template(positive_template, values)
        negative = render_template(negative_template, values)
        warnings = []
        if int(total) > 3 and not values["secondary_character_group_spec"].strip():
            warnings.append("n_total exceeds 3; describe the additional people in secondary_character_group_spec.")
        for label, prompt in (("Positive", positive), ("Negative", negative)):
            if "{{" in prompt or "}}" in prompt:
                warnings.append(f"{label}: unresolved placeholder-like text remains; check inputs and template syntax.")
        return positive, negative, "\n".join(warnings) or "OK"
