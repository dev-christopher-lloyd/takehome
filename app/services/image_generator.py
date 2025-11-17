from __future__ import annotations
import os
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


class ImageGenerator(Protocol):
  def generate(self, prompt: str, aspect_ratio: str, images: list | None = None) -> ImageResult:
    raise NotImplementedError(
        "Subclasses should implement the 'generate' method.")


class DummyImageGenerator:
  def generate(self, prompt: str, aspect_ratio: str, images: list | None = None) -> ImageResult:
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
  def __init__(self):
    self.client = genai.Client()
  def generate(self, prompt: str, aspect_ratio: str, images: list | None = None) -> ImageResult:
    # add reference images to call if they exist
    if images is not None:
      images = [Image.open(BytesIO(image)) for image in images]
      contents = images + [prompt]
    else:
      contents = [prompt]
    response = self.client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents, # type: ignore
        config=types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        )
    )

    image_parts = [
        part.inline_data.data  # type: ignore
        for part in response.candidates[0].content.parts  # type: ignore
        if getattr(part, "inline_data", None)
    ]

    if not image_parts:
      raise RuntimeError("No image data found in Gemini response.")

    image_bytes = bytes(image_parts[0])  # type: ignore

    img = Image.open(BytesIO(image_bytes))  # type: ignore
    width, height = img.size

    # type: ignore
    return ImageResult(content=image_bytes, width=width, height=height, model_name="gemini")

# Factory method to return the appropriate image generator.
# right now it just checks if the gemini api key exists in .env,
# but could be extended for adding more models
def get_image_generator() -> ImageGenerator:
  if "GEMINI_API_KEY" in os.environ:
    return GoogleGeminiNanoBananaGenerator()
  return DummyImageGenerator()
