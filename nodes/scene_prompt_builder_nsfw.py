"""Build Scene with an independently editable template module."""

from . import scene_templates_nsfw
from .scene_prompt_builder import ScenePromptTemplate


class ScenePromptTemplateNSFW(ScenePromptTemplate):
    TEMPLATE_MODULE = scene_templates_nsfw
