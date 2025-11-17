from __future__ import annotations
import os
from typing import Protocol
from dataclasses import dataclass
from google import genai


@dataclass
class TextResult:
  content: str
  model_name: str


class TextGenerator(Protocol):
  def generate(self, prompt: str) -> TextResult:
    raise NotImplementedError(
        "Subclasses should implement the 'generate' method.")


class DummyTextGenerator:
  def generate(self, prompt: str) -> TextResult:
    return TextResult(content="Test output", model_name="dummy")


class GoogleGeminiFlashGenerator:
    def __init__(self):
      self.client = genai.Client()
    def generate(self, prompt: str) -> TextResult:
      response = self.client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
      )
      return TextResult(content=response.text, model_name="gemini-2.5-flash") # type: ignore


# Factory method to return the appropriate text generator.
# right now it just checks if the gemini api key exists in .env,
# but could be extended for adding more models
def get_text_generator() -> TextGenerator:
  if "GEMINI_API_KEY" in os.environ:
    return GoogleGeminiFlashGenerator()
  return DummyTextGenerator()
