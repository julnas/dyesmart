# backend/color_segmentation.py
import numpy as np
import colorsys
from typing import Dict, List
from PIL import Image
import io


class HairColorSegmenter:
    def __init__(self):
        self.depth_levels = {
            1: {"name": "Schwarz", "min_brightness": 0, "max_brightness": 20},
            2: {"name": "Sehr dunkelbraun", "min_brightness": 20, "max_brightness": 35},
            3: {"name": "Dunkelbraun", "min_brightness": 35, "max_brightness": 50},
            4: {"name": "Mittelbraun", "min_brightness": 50, "max_brightness": 65},
            5: {"name": "Hellbraun", "min_brightness": 65, "max_brightness": 80},
            6: {"name": "Dunkelblond", "min_brightness": 80, "max_brightness": 100},
            7: {"name": "Mittelblond", "min_brightness": 100, "max_brightness": 130},
            8: {"name": "Hellblond", "min_brightness": 130, "max_brightness": 160},
            9: {"name": "Sehr hellblond", "min_brightness": 160, "max_brightness": 190},
            10: {"name": "Platinblond", "min_brightness": 190, "max_brightness": 255},
        }

        self.nuance_levels = {
            0.0: "Neutral",
            0.1: "Asch",
            0.3: "Gold",
            0.4: "Kupfer",
            0.6: "Rot",
            0.7: "Violett",
            0.8: "Blau",
        }

    def rgb_to_hsv(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return h * 360, s * 100, v * 100

    def brightness(self, rgb):
        return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

    def classify(self, rgb: List[int]) -> Dict:
        h, s, v = self.rgb_to_hsv(rgb)
        bright = self.brightness(rgb)

        depth = 5
        depth_name = "Unbekannt"
        for d, info in self.depth_levels.items():
            if info["min_brightness"] <= bright <= info["max_brightness"]:
                depth = d
                depth_name = info["name"]
                break

        nuance = 0.0
        if s > 25:
            if h < 15 or h > 350:
                nuance = 0.6
            elif 15 <= h < 35:
                nuance = 0.4
            elif 35 <= h < 60:
                nuance = 0.3
            elif 80 <= h < 150:
                nuance = 0.1
            elif 150 <= h < 200:
                nuance = 0.7
            elif 200 <= h < 260:
                nuance = 0.8

        return {
            "source_depth": depth,
            "source_nuance": nuance,
            "avg_color": [int(rgb[0]), int(rgb[1]), int(rgb[2])],
            "depth_name": depth_name,
            "nuance_name": self.nuance_levels.get(nuance, "Neutral"),
            "info": f"{depth_name}, Nuance {self.nuance_levels.get(nuance, 'Neutral')}",
        }


_segmenter = HairColorSegmenter()


def analyze_image_average_rgb_from_pil(img: Image.Image) -> List[int]:
    img = img.convert("RGB")
    w, h = img.size
    img = img.crop((0, 0, w, h // 2))  # obere Hälfte
    arr = np.array(img)
    avg = arr.mean(axis=(0, 1))
    return [int(avg[0]), int(avg[1]), int(avg[2])]


def analyze_hair_color_from_bytes(image_bytes: bytes) -> Dict:
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return {"error": "Bild konnte nicht gelesen werden"}

    rgb = analyze_image_average_rgb_from_pil(img)
    return _segmenter.classify(rgb)
