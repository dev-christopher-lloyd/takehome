from __future__ import annotations
from typing import Optional, Protocol
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from google import genai
from google.genai import types

@dataclass
class ImageResult:
    content: bytes
    width: int
    height: int
    model_name: str
    seed: Optional[int] = None

class ImageGenerator(Protocol):
    def generate(self, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        raise NotImplementedError("Subclasses should implement the 'generate' method.")

class DummyImageGenerator:
    def generate(self, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        # Map aspect ratio string to a basic size
        if aspect_ratio == "1:1":
            size = (1024, 1024)
        elif aspect_ratio == "9:16":
            size = (768, 1365)
        elif aspect_ratio == "16:9":
            size = (1365, 768)
        else:
            # default square
            size = (1024, 1024)

        img = Image.new("RGB", size, color=(40, 40, 60))
        draw = ImageDraw.Draw(img)

        # Basic text overlay: center-ish prompt summary
        text = prompt[:120] + ("..." if len(prompt) > 120 else "")
        try:
            font = ImageFont.load_default()
        except Exception:  # pragma: no cover
            font = None  # type: ignore[assignment]

        text_box = draw.textbbox((0, 0), text, font=font) if font else (0, 0, 0, 0)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2

        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageResult(content=buf.getvalue(), width=size[0], height=size[1], model_name="dummy")

class GoogleGeminiNanoBananaGenerator:
    def generate(self, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
                seed=seed
            )
        )
        
        image_parts = [
            part.inline_data.data # type: ignore
            for part in response.candidates[0].content.parts # type: ignore
            if getattr(part, "inline_data", None)
        ]

        if not image_parts:
            raise RuntimeError("No image data found in Gemini response.")
        
        image_bytes = bytes(image_parts[0]) # type: ignore
        
        img = Image.open(BytesIO(image_bytes)) # type: ignore
        width, height = img.size

        return ImageResult(content=image_bytes, width=width, height=height, model_name="gemini") # type: ignore

# Factory method to return the appropriate image generator.
def get_image_generator() -> ImageGenerator:
    #return DummyImageGenerator()
    return GoogleGeminiNanoBananaGenerator()