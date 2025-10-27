"""Gemini client."""

import copy
from typing import Any, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from ...config import settings
from ...logging import get_logger

logger = get_logger(__name__)


def _resolve_refs(schema_dict: dict, definitions: dict) -> dict:
    """
    Recursively resolve $ref references in a JSON schema.
    
    Args:
        schema_dict: Schema dictionary that may contain $ref.
        definitions: Dictionary of definitions to resolve references from.
    
    Returns:
        Schema with all $ref resolved.
    """
    if isinstance(schema_dict, dict):
        # If this is a $ref, resolve it
        if "$ref" in schema_dict:
            ref_path = schema_dict["$ref"]
            # Extract the definition name (e.g., "#/$defs/SCTQuestion" -> "SCTQuestion")
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.split("/")[-1]
                if def_name in definitions:
                    # Return a resolved copy of the definition
                    resolved = definitions[def_name].copy()
                    return _resolve_refs(resolved, definitions)
            return schema_dict
        
        # Recursively resolve in nested dictionaries
        result = {}
        for key, value in schema_dict.items():
            if isinstance(value, dict):
                result[key] = _resolve_refs(value, definitions)
            elif isinstance(value, list):
                result[key] = [
                    _resolve_refs(item, definitions) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    return schema_dict


def _clean_schema_for_gemini(schema_dict: dict) -> dict:
    """
    Clean and prepare a JSON schema for Gemini API.
    
    This function:
    1. Resolves all $ref references by inlining definitions
    2. Removes fields not supported by Gemini
    
    Args:
        schema_dict: Dictionary representation of a JSON schema.

    Returns:
        Cleaned schema dictionary ready for Gemini.
    """
    # Make a deep copy to avoid modifying the original
    schema_copy = copy.deepcopy(schema_dict)
    
    # Extract $defs if present
    definitions = schema_copy.pop("$defs", {})
    
    # Resolve all $ref references
    if definitions:
        schema_copy = _resolve_refs(schema_copy, definitions)
    
    # Now clean unsupported fields recursively
    def clean_fields(obj):
        if isinstance(obj, dict):
            # Remove fields not supported by Gemini
            obj.pop("examples", None)
            obj.pop("example", None)
            obj.pop("title", None)
            obj.pop("description", None)
            obj.pop("$defs", None)
            
            # Recursively clean nested objects
            for key, value in obj.items():
                if isinstance(value, dict):
                    obj[key] = clean_fields(value)
                elif isinstance(value, list):
                    obj[key] = [
                        clean_fields(item) if isinstance(item, dict) else item
                        for item in value
                    ]
        return obj
    
    return clean_fields(schema_copy)


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
