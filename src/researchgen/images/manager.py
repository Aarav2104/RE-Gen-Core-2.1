"""Manages uploaded figures/images separately from text sources, assigning
figure numbers and tracking placement preferences."""
from __future__ import annotations

from typing import List, Optional
from researchgen.models import ImageAsset


class ImageManager:
    def __init__(self):
        self.images: List[ImageAsset] = []

    def add(self, image: ImageAsset) -> ImageAsset:
        image.figure_number = len(self.images) + 1
        self.images.append(image)
        return image

    def for_section(self, section_name: str) -> List[ImageAsset]:
        return [
            img for img in self.images
            if img.preferred_section and img.preferred_section.strip().lower() == section_name.strip().lower()
        ]

    def unassigned(self) -> List[ImageAsset]:
        return [img for img in self.images if not img.preferred_section]

    def caption_line(self, image: ImageAsset) -> str:
        cap = image.caption.strip() or image.filename
        return f"Figure {image.figure_number}: {cap}"
