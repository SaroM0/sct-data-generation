"""SCT Item Generator using OpenAI or Gemini Structured Outputs."""

from pathlib import Path
from typing import Optional

from ..llm.gemini import GeminiClient
from ..llm.openai import OpenAIClient
from ..logging import get_logger
from ..schemas import SCTItem
from ..validators import validate_sct_item
from ..validators.utils import save_validated_sct

logger = get_logger(__name__)


class SCTGenerator:
    """
    Generator for Script Concordance Test (SCT) items.

    Uses OpenAI or Gemini structured outputs to ensure valid SCT item generation.
    """

    def __init__(self, provider: str = "openai"):
        """
        Initialize SCT generator.

        Args:
            provider: LLM provider to use ("openai" or "gemini").
        """
        self.provider = provider.lower()

        if self.provider == "openai":
            self.client = OpenAIClient()
        elif self.provider == "gemini":
            self.client = GeminiClient()
        else:
            raise ValueError(
                f"Invalid provider: {provider}. Must be 'openai' or 'gemini'"
            )

        # Load XML prompt template
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt_template_path = prompts_dir / "sct_item_prompt.xml"

        if not self.prompt_template_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {self.prompt_template_path}"
            )

        # Load the XML template
        with open(self.prompt_template_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

        logger.info(f"SCT Generator initialized with provider: {self.provider}")

    def _render_prompt(
        self,
        topic: Optional[str],
        domain: Optional[str],
        difficulty: Optional[str],
        additional_context: Optional[str],
    ) -> str:
        """
        Render the SCT item generation prompt from XML template.

        Args:
            topic: Specific topic for the SCT item.
            domain: Clinical domain/subdomain.
            difficulty: Difficulty level.
            additional_context: Additional context for generation.

        Returns:
            Rendered prompt string.
        """
        # Build parameters list
        parameters = []

        if topic:
            parameters.append(f"<topic>{topic}</topic>")

        if domain:
            parameters.append(f"<domain>{domain}</domain>")

        if difficulty:
            parameters.append(f"<difficulty>{difficulty}</difficulty>")

        if additional_context:
            parameters.append(
                f"<additional_context>{additional_context}</additional_context>"
            )

        # Create parameters content
        if parameters:
            parameters_content = "\n      ".join(parameters)
        else:
            parameters_content = "<note>No specific parameters provided</note>"

        # Replace the single placeholder - much more robust than matching multiline blocks
        rendered = self.prompt_template.replace("{{PARAMETERS}}", parameters_content)

        # Verify the replacement worked
        if "{{PARAMETERS}}" in rendered:
            logger.warning(
                "Failed to replace {{PARAMETERS}} placeholder in template. "
                "Check that the template contains the placeholder."
            )

        logger.debug("Prompt rendered successfully from XML template")
        return rendered

    def generate(
        self,
        model: str,
        topic: Optional[str] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> SCTItem:
        """
        Generate a complete SCT item.

        The item is automatically saved to data/generated/ folder.

        Args:
            model: LLM model to use (must support structured outputs).
            topic: Specific topic for the SCT item (e.g., "spontaneous bacterial peritonitis").
            domain: Clinical domain (e.g., "Cirrhosis_Complications").
            difficulty: Difficulty level (e.g., "intermediate", "advanced").
            additional_context: Additional context to guide generation.

        Returns:
            Generated SCTItem with all fields populated.

        Raises:
            ValueError: If model refuses the request.
        """
        logger.info(f"Starting SCT item generation with {self.provider}")
        logger.info(f"Parameters - model: {model}, topic: {topic}, domain: {domain}")

        # Render prompt
        prompt = self._render_prompt(topic, domain, difficulty, additional_context)

        # Generate using structured outputs
        instructions = (
            "Generate a complete SCT item in English about hepatology "
            "following EXACTLY the format and quality criteria provided. "
            "Ensure all fields meet the quality specifications."
        )

        try:
            sct_item = self.client.parse_simple(
                input_text=prompt,
                model_class=SCTItem,
                model=model,
                instructions=instructions,
            )

            logger.info(f"SCT item generated successfully - domain: {sct_item.domain}")
            logger.debug(f"Vignette length: {len(sct_item.vignette.split())} words")

            # Validate the generated item
            logger.info("Validating generated SCT item...")
            validation_result = validate_sct_item(sct_item)

            if not validation_result.is_valid:
                logger.error(
                    f"Validation failed with {len(validation_result.errors)} error(s)"
                )
                for error in validation_result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("✓ Validation passed")
                if validation_result.warnings:
                    logger.info(
                        f"Validation warnings: {len(validation_result.warnings)}"
                    )
                    for warning in validation_result.warnings:
                        logger.warning(f"  - {warning}")

            # Save the item to appropriate folders
            save_validated_sct(sct_item, validation_result)

            return sct_item

        except ValueError as e:
            logger.error(f"Model refused request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating SCT item: {e}")
            raise


def generate_sct_item(
    model: str,
    provider: str = "openai",
    topic: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> SCTItem:
    """
    Convenience function to generate a single SCT item.

    Args:
        model: LLM model to use (must support structured outputs).
        provider: LLM provider to use ("openai" or "gemini").
        topic: Specific topic for the SCT item.
        domain: Clinical domain.
        difficulty: Difficulty level.
        additional_context: Additional context.

    Returns:
        Generated SCTItem.
    """
    generator = SCTGenerator(provider=provider)
    return generator.generate(model, topic, domain, difficulty, additional_context)
