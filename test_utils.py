from src.functions.vision import SingleImageAnalysis, ImageSetAnalysis

def create_single_image_analysis(description="A test image", objects=None, colors=None, scene_type="indoor", quality="high"):
    """Factory function to create SingleImageAnalysis instances."""
    if objects is None:
        objects = ["object1", "object2"]
    if colors is None:
        colors = ["red", "blue"]
    
    return SingleImageAnalysis(
        description=description,
        objects=objects,
        colors=colors,
        scene_type=scene_type,
        quality=quality,
        metadata={"key": "value"}
    )

def create_image_set_analysis(summary="A summary", common_objects=None, comparative_analysis="Comparison"):
    """Factory function to create ImageSetAnalysis instances."""
    if common_objects is None:
        common_objects = ["object1", "object2"]
    
    return ImageSetAnalysis(
        summary=summary,
        common_objects=common_objects,
        comparative_analysis=comparative_analysis
    ) 