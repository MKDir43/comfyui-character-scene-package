from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps


SUPPORTED_IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
)


class ImagePromptPackageLoader:
    """
    Loads:

        <root_path>/<package_name>/image.*
        <root_path>/<package_name>/positive.txt
        <root_path>/<package_name>/negative.txt

    Outputs:

        IMAGE
        positive STRING
        negative STRING
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "root_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    },
                ),
                "package_name": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    },
                ),
            }
        }

    RETURN_TYPES = (
        "IMAGE",
        "STRING",
        "STRING",
    )

    RETURN_NAMES = (
        "image",
        "positive_prompt",
        "negative_prompt",
    )

    FUNCTION = "load_package"

    CATEGORY = "Character Scene Tools/References"

    def load_package(
        self,
        root_path: str,
        package_name: str,
    ):
        # ---------------------------------------
        # Resolve paths
        # ---------------------------------------

        root = Path(root_path).expanduser().resolve()

        if not root.is_dir():
            raise FileNotFoundError(
                f"Root directory does not exist: {root}"
            )

        package_dir = (root / package_name).resolve()

        # Prevent "../../..." from escaping root.
        try:
            package_dir.relative_to(root)
        except ValueError:
            raise ValueError(
                "package_name must point inside root_path."
            )

        if not package_dir.is_dir():
            raise FileNotFoundError(
                f"Package directory does not exist: {package_dir}"
            )

        # ---------------------------------------
        # Find image
        # ---------------------------------------

        image_path = None

        for extension in SUPPORTED_IMAGE_EXTENSIONS:
            candidate = package_dir / f"image{extension}"

            if candidate.is_file():
                image_path = candidate
                break

        if image_path is None:
            raise FileNotFoundError(
                f"No reference image found in {package_dir}. "
                "Expected image.png, image.jpg, "
                "image.jpeg or image.webp."
            )

        # ---------------------------------------
        # Load image
        # ---------------------------------------

        pil_image = Image.open(image_path)

        pil_image = ImageOps.exif_transpose(pil_image)
        pil_image = pil_image.convert("RGB")

        image_array = np.asarray(
            pil_image,
            dtype=np.float32,
        )

        image_array /= 255.0

        # ComfyUI IMAGE format:
        #
        # [batch, height, width, channels]
        #
        # Example:
        # [1, 1024, 1024, 3]

        image_tensor = torch.from_numpy(
            image_array
        ).unsqueeze(0)

        # ---------------------------------------
        # Load prompts
        # ---------------------------------------

        positive_path = package_dir / "positive.txt"
        negative_path = package_dir / "negative.txt"

        positive_prompt = self._read_text(
            positive_path
        )

        negative_prompt = self._read_text(
            negative_path
        )

        return (
            image_tensor,
            positive_prompt,
            negative_prompt,
        )

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.is_file():
            return ""

        return path.read_text(
            encoding="utf-8"
        ).strip()
