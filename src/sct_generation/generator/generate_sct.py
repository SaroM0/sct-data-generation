"""SCT Item Generator using OpenAI Structured Outputs."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from ..llm import OpenAIClient
from ..logging import get_logger
from ..schemas import SCTItem
from ..validators import validate_sct_item
from .utils import save_sct_item

logger = get_logger(__name__)


class SCTGenerator:
    """
    Generator for Script Concordance Test (SCT) items.

    Uses OpenAI's structured outputs to ensure valid SCT item generation.
    """

    def __init__(self):
        """Initialize SCT generator."""
        self.client = OpenAIClient()

        # Setup Jinja2 for prompt templates
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info("SCT Generator initialized")

    def _render_prompt(
        self,
        topic: Optional[str],
        domain: Optional[str],
        difficulty: Optional[str],
        additional_context: Optional[str],
    ) -> str:
        """
        Render the SCT item generation prompt.

        Args:
            topic: Specific topic for the SCT item.
            domain: Clinical domain/subdomain.
            difficulty: Difficulty level.
            additional_context: Additional context for generation.

        Returns:
            Rendered prompt string.
        """
        template = self.jinja_env.get_template("sct_item_prompt.j2")

        rendered = template.render(
            topic=topic,
            domain=domain,
            difficulty=difficulty,
            additional_context=additional_context,
        )

        logger.debug("Prompt rendered successfully")
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
            model: OpenAI model to use (must support structured outputs).
            topic: Specific topic for the SCT item (e.g., "spontaneous bacterial peritonitis").
            domain: Clinical domain (e.g., "Cirrhosis_Complications").
            difficulty: Difficulty level (e.g., "intermediate", "advanced").
            additional_context: Additional context to guide generation.

        Returns:
            Generated SCTItem with all fields populated.

        Raises:
            ValueError: If model refuses the request.
        """
        logger.info("Starting SCT item generation")
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
                # Still save the item but log that it failed validation
                logger.warning(
                    "Item will be saved despite validation errors for review"
                )
            else:
                logger.info("✓ Validation passed")
                if validation_result.warnings:
                    logger.info(
                        f"Validation warnings: {len(validation_result.warnings)}"
                    )
                    for warning in validation_result.warnings:
                        logger.warning(f"  - {warning}")

            # Automatically save the item
            output_path = save_sct_item(sct_item)
            logger.info(f"Item automatically saved to: {output_path}")

            return sct_item

        except ValueError as e:
            logger.error(f"Model refused request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating SCT item: {e}")
            raise


def generate_sct_item(
    model: str,
    topic: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> SCTItem:
    """
    Convenience function to generate a single SCT item.

    Args:
        model: OpenAI model to use (must support structured outputs).
        topic: Specific topic for the SCT item.
        domain: Clinical domain.
        difficulty: Difficulty level.
        additional_context: Additional context.

    Returns:
        Generated SCTItem.
    """
    generator = SCTGenerator()
    return generator.generate(model, topic, domain, difficulty, additional_context)
