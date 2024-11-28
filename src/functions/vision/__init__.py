"""Vision analysis functions."""
from .image_analysis import (
    ImageAnalyzer,
    SingleImageAnalysis,
    ImageSetAnalysis,
    encode_image_to_base64,
)
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ImageAnalysisResponse:
    """Response structure for image analysis results."""
    description: str
    tags: List[str]
    objects: List[str]
    text: Optional[str] = None
    faces: Optional[List[dict]] = None
    colors: Optional[List[str]] = None
    landmarks: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None

__all__ = [
    "ImageAnalyzer",
    "SingleImageAnalysis",
    "ImageSetAnalysis",
    "encode_image_to_base64",
] 