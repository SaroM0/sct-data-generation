"""Service layer for text generation using Gemini."""

from typing import Any, Type

from pydantic import BaseModel

from .gemini_client import GeminiClient


def generate_text(
    prompt: str,
    model: str,
    instructions: str,
) -> str:
    """
    Quick text generation function.

    Args:
        prompt: Input prompt.
        model: Model to use for generation.
        instructions: System instructions for the model.

    Returns:
        Generated text.
    """
    client = GeminiClient()
    return client.generate_simple(prompt, model, instructions)


def parse_structured(
    prompt: str,
    model_class: Type[BaseModel],
    model: str,
    instructions: str,
) -> Any:
    """
    Quick structured generation function.

    Args:
        prompt: Input prompt.
        model_class: Pydantic model class defining the output schema.
        model: Model to use (must support structured outputs).
        instructions: System instructions for the model.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        ValueError: If model refused the request or parsing failed.
    """
    client = GeminiClient()
    return client.parse_simple(prompt, model_class, model, instructions)
