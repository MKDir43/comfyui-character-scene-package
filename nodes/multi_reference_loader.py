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

MAX_PACKAGES = 5


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------

def load_image(path: Path) -> torch.Tensor:
    image = Image.open(path)

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    array = np.asarray(
        image,
        dtype=np.float32,
    )

    array /= 255.0

    # ComfyUI IMAGE:
    # [batch, height, width, channels]

    return torch.from_numpy(
        array
    ).unsqueeze(0)


def load_text(path: Path) -> str:
    if not path.is_file():
        return ""

    return path.read_text(
        encoding="utf-8"
    ).strip()


def find_package_image(
    package_dir: Path,
) -> Path:

    for extension in SUPPORTED_IMAGE_EXTENSIONS:

        path = package_dir / f"image{extension}"

        if path.is_file():
            return path

    raise FileNotFoundError(
        f"No image found in package: {package_dir}"
    )


def empty_image() -> torch.Tensor:
    """
    Placeholder for unused image outputs.

    1x1 black RGB image.
    """

    return torch.zeros(
        (1, 1, 1, 3),
        dtype=torch.float32,
    )


# ---------------------------------------------------------
# Node
# ---------------------------------------------------------

class MultiPromptPackageLoader:

    @classmethod
    def INPUT_TYPES(cls):

        package_inputs = {}

        for i in range(1, MAX_PACKAGES + 1):

            package_inputs[f"package_{i}"] = (
                "STRING",
                {
                    "default": "None",
                    "multiline": False,
                },
            )

        return {
            "required": {
                "root_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    },
                ),

                **package_inputs,
            }
        }

    # -----------------------------------------------------
    # Outputs
    # -----------------------------------------------------

    RETURN_TYPES = (
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",

        "STRING",
        "STRING",

        "INT",
        "STRING",
    )

    RETURN_NAMES = (
        "image_02",
        "image_03",
        "image_04",
        "image_05",
        "image_06",

        "character_positive",
        "character_negative",

        "character_count",
        "character_mapping",
    )

    FUNCTION = "load_packages"

    CATEGORY = "ComfyUI Character Scene Package/References"

    # -----------------------------------------------------
    # Main
    # -----------------------------------------------------

    def load_packages(
        self,
        root_path,
        package_1,
        package_2,
        package_3,
        package_4,
        package_5,
    ):

        root = Path(
            root_path
        ).expanduser().resolve()

        if not root.is_dir():

            raise FileNotFoundError(
                f"Root path does not exist: {root}"
            )

        package_names = [
            package_1,
            package_2,
            package_3,
            package_4,
            package_5,
        ]

        # -------------------------------------------------
        # Remove disabled slots.
        # -------------------------------------------------

        enabled_packages = []

        for name in package_names:

            name = name.strip()

            if not name:
                continue

            if name.lower() == "none":
                continue

            enabled_packages.append(name)

        # -------------------------------------------------
        # Outputs
        # -------------------------------------------------

        images = []

        positive_sections = []
        negative_sections = []
        mapping_sections = []

        # -------------------------------------------------
        # Load enabled packages.
        # -------------------------------------------------

        for index, package_name in enumerate(
            enabled_packages
        ):

            # index:
            # 0 -> Character A -> Image 02
            # 1 -> Character B -> Image 03
            # 2 -> Character C -> Image 04

            character_letter = chr(
                ord("A") + index
            )

            image_number = index + 2

            package_dir = (
                root / package_name
            ).resolve()

            # Security / path sanity check.
            try:
                package_dir.relative_to(root)

            except ValueError:

                raise ValueError(
                    f"Package escapes root path: "
                    f"{package_name}"
                )

            if not package_dir.is_dir():

                raise FileNotFoundError(
                    f"Package not found: "
                    f"{package_dir}"
                )

            # ---------------------------------------------
            # Image
            # ---------------------------------------------

            image_path = find_package_image(
                package_dir
            )

            images.append(
                load_image(image_path)
            )

            # ---------------------------------------------
            # Prompt
            # ---------------------------------------------

            positive = load_text(
                package_dir / "positive.txt"
            )

            negative = load_text(
                package_dir / "negative.txt"
            )

            positive_section = (
                f"CHARACTER {character_letter} "
                f"— DESIGN SOURCE: IMAGE {image_number:02d} ONLY\n\n"
                f"{positive}\n\n"
                "IDENTITY LOCK: Use only the assigned reference for this "
                "character's design; do not borrow traits from other references."
            )

            negative_section = (
                f"CHARACTER {character_letter} "
                f"— IMAGE {image_number:02d}\n\n"
                f"{negative}"
            )

            mapping_sections.append(
                f"Character {character_letter} = Image {image_number:02d}"
            )

            positive_sections.append(
                positive_section
            )

            negative_sections.append(
                negative_section
            )

        # -------------------------------------------------
        # Fill unused image outputs.
        # -------------------------------------------------

        while len(images) < MAX_PACKAGES:

            images.append(
                empty_image()
            )

        # -------------------------------------------------
        # Merge prompt sections.
        # -------------------------------------------------

        character_positive = (
            "\n\n".join(
                positive_sections
            )
        )

        character_negative = (
            "\n\n".join(
                negative_sections
            )
        )

        character_count = len(
            enabled_packages
        )

        return (
            images[0],
            images[1],
            images[2],
            images[3],
            images[4],

            character_positive,
            character_negative,

            character_count,
            "\n".join(mapping_sections),
        )


# ---------------------------------------------------------
# Registration
# ---------------------------------------------------------
