"""Structural markers are independent of editable prompt prose."""

import re

MARKER = re.compile(r"(?m)^\{\{(?:GROUP_RULES_START|SCENE_SLOT_[ABC]|CHARACTER_SLOT_[ABC]|CHARACTER_EXTRA_START)\}\}\r?\n?")


def strip_markers(template):
    return MARKER.sub("", template)


def split_marker(template, name):
    token = "{{" + name + "}}\n"
    normalized = template.replace("\r\n", "\n")
    if normalized.count(token) != 1:
        raise ValueError(f"Template must contain exactly one standalone marker: {{{{{name}}}}}")
    before, after = normalized.split(token, 1)
    if before and not before.endswith("\n"):
        raise ValueError(f"Template marker must be on its own line: {{{{{name}}}}}")
    return before, after
