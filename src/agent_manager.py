from typing import List, Union
from pathlib import Path
import instructor
from pydantic import HttpUrl
from .functions.vision import ImageAnalysisResponse, analyze_images
from .aoai.client import AOAIClient

class VisionAgent:
    """Agent for handling vision-related tasks."""
    
    def __init__(self, client: AOAIClient):
        # Patch the client with instructor
        self.client = instructor.patch(client)

    async def analyze_images(
        self,
        images: List[Union[str, Path, HttpUrl]],
        max_tokens: int = 2000
    ) -> ImageAnalysisResponse:
        """Analyze one or more images.
        
        Args:
            images: List of image paths or URLs
            max_tokens: Maximum tokens for response
            
        Returns:
            Structured analysis of the images
        """
        return await analyze_images(self.client, images, max_tokens) 