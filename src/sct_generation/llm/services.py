"""Service layer for text generation using OpenAI."""

from typing import Any, Type

from pydantic import BaseModel

from .openai_client import OpenAIClient


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
        instructions: Instructions for the model.

    Returns:
        Generated text.
    """
    client = OpenAIClient()
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
        instructions: Instructions for the model.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        ValueError: If model refused the request.
    """
    client = OpenAIClient()
    return client.parse_simple(prompt, model_class, model, instructions)
