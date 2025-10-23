"""OpenAI client."""

from typing import Any, Type

from openai import OpenAI
from pydantic import BaseModel

from ..config import settings
from ..logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """
    Client for OpenAI Responses API.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        self.api_key = settings.openai_api_key

        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            )

        self._client = OpenAI(api_key=self.api_key)

        logger.info("OpenAI client initialized")

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
            instructions: Instructions for the model.

        Returns:
            Generated text as a string.
        """
        try:
            params = {
                "model": model,
                "input": input_text,
                "instructions": instructions,
            }

            logger.info(f"Generating text with model: {model}")
            logger.debug(f"Request params: {params}")

            response = self._client.responses.create(**params)
            output_text = getattr(response, "output_text", "")

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
            instructions: Instructions for the model.

        Returns:
            Parsed Pydantic model instance.

        Raises:
            ValueError: If model refused the request.
        """
        try:
            params = {
                "model": model,
                "input": input_text,
                "text_format": model_class,
                "instructions": instructions,
            }

            logger.info(f"Generating structured output with model: {model}")
            logger.debug(f"Request params: {params}")

            response = self._client.responses.parse(**params)

            # Check for refusal
            refusal = None
            for item in response.output:
                for content in item.content:
                    if content.type == "refusal":
                        refusal = getattr(content, "refusal", None)
                        break

            if refusal:
                logger.warning(f"Model refused request: {refusal}")
                raise ValueError(f"Model refused request: {refusal}")

            output_parsed = getattr(response, "output_parsed", None)

            logger.info("Structured generation successful")

            return output_parsed

        except Exception as e:
            logger.error(f"Error generating structured output: {e}")
            raise
