# backend/image_analysis.py
from color_segmentation import analyze_hair_color_from_bytes

def analyze_hair_image_simple(image_bytes: bytes):
    return analyze_hair_color_from_bytes(image_bytes)
