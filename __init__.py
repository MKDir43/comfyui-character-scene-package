"""ComfyUI entry point for ComfyUI Character Scene Package.

Keep serialized node IDs stable so existing workflows continue to load.
"""

from .nodes.reference_loader import ImagePromptPackageLoader
from .nodes.multi_reference_loader import MultiPromptPackageLoader
from .nodes.scene_prompt_builder import ScenePromptTemplate
from .nodes.scene_prompt_builder_nsfw import ScenePromptTemplateNSFW

NODE_CLASS_MAPPINGS = {
    "ImagePromptPackageLoader": ImagePromptPackageLoader,
    "MultiPromptPackageLoader": MultiPromptPackageLoader,
    "ScenePromptTemplate": ScenePromptTemplate,
    "ScenePromptTemplateNSFW": ScenePromptTemplateNSFW,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagePromptPackageLoader": "Load Character Reference",
    "MultiPromptPackageLoader": "Load Character References (Up to 5)",
    "ScenePromptTemplate": "Build Scene Prompts",
    "ScenePromptTemplateNSFW": "Build Scene Prompts (NSFW)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
