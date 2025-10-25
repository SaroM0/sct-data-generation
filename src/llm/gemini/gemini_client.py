"""Gemini client."""

from typing import Any, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from ...config import settings
from ...logging import get_logger

logger = get_logger(__name__)


def _clean_schema_for_gemini(schema_dict: dict) -> dict:
    """
    Remove fields not supported by Gemini from a JSON schema.

    Args:
        schema_dict: Dictionary representation of a JSON schema.

    Returns:
        Cleaned schema dictionary.
    """
    if isinstance(schema_dict, dict):
        # Remove fields not supported by Gemini
        schema_dict.pop("examples", None)
        schema_dict.pop("example", None)
        schema_dict.pop("title", None)
        schema_dict.pop("description", None)

        # Recursively clean nested schemas
        for key, value in schema_dict.items():
            if isinstance(value, dict):
                schema_dict[key] = _clean_schema_for_gemini(value)
            elif isinstance(value, list):
                schema_dict[key] = [
                    _clean_schema_for_gemini(item) if isinstance(item, dict) else item
                    for item in value
                ]

    return schema_dict


class GeminiClient:
    """
    Client for Google Gemini API.
    """

    def __init__(self):
        """Initialize Gemini client."""
        self.api_key = settings.gemini_api_key

        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable."
            )

        self._client = genai.Client(api_key=self.api_key)

        logger.info("Gemini client initialized")

    def generate_simple(
        self,
        input_text: str,
        model: str,
        instructions: str,
    ) -> str:
        """
        Simple text generation.

        Args:
            input_text: Input prompt text.
            model: Model to use for generation.
            instructions: System instructions for the model.

        Returns:
            Generated text as a string.
        """
        try:
            config = types.GenerateContentConfig(
                system_instruction=instructions,
            )

            logger.info(f"Generating text with model: {model}")
            logger.debug(f"Input text length: {len(input_text)}")

            response = self._client.models.generate_content(
                model=model,
                contents=input_text,
                config=config,
            )

            output_text = response.text

            logger.info(f"Generation successful. Output length: {len(output_text)}")

            return output_text

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def parse_simple(
        self,
        input_text: str,
        model_class: Type[BaseModel],
        model: str,
        instructions: str,
    ) -> Any:
        """
        Structured generation with JSON Schema.

        Args:
            input_text: Input prompt text.
            model_class: Pydantic model class defining the output schema.
            model: Model to use for generation.
            instructions: System instructions for the model.

        Returns:
            Parsed Pydantic model instance.

        Raises:
            ValueError: If model refused the request or parsing failed.
        """
        try:
            # Get the JSON schema from Pydantic model and clean it for Gemini
            json_schema = model_class.model_json_schema()
            cleaned_schema = _clean_schema_for_gemini(json_schema)

            config = types.GenerateContentConfig(
                system_instruction=instructions,
                response_mime_type="application/json",
                response_schema=cleaned_schema,
            )

            logger.info(f"Generating structured output with model: {model}")
            logger.debug(f"Input text length: {len(input_text)}")
            logger.debug(f"Output schema: {model_class.__name__}")

            response = self._client.models.generate_content(
                model=model,
                contents=input_text,
                config=config,
            )

            # Get the text response and parse it manually with Pydantic
            response_text = response.text

            # Parse the JSON response with the Pydantic model
            output_parsed = model_class.model_validate_json(response_text)

            logger.info("Structured generation successful")

            return output_parsed

        except Exception as e:
            logger.error(f"Error generating structured output: {e}")
            raise
