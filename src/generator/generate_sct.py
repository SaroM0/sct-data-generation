"""SCT Item Generator using OpenAI or Gemini Structured Outputs."""

from pathlib import Path
from typing import Literal, Optional

from ..llm.gemini import GeminiClient
from ..llm.openai import OpenAIClient
from ..logging import get_logger
from ..schemas import SCTItem
from ..validators import validate_sct_item
from ..validators.utils import save_validated_sct

logger = get_logger(__name__)

# Type for guideline selection
GuidelineType = Literal["american", "british", "european"]


class SCTGenerator:
    """
    Generator for Script Concordance Test (SCT) items.

    Uses OpenAI or Gemini structured outputs to ensure valid SCT item generation.
    Can combine the base SCT prompt with clinical guidelines for context.
    """

    def __init__(
        self, provider: str = "openai", guideline: Optional[GuidelineType] = None
    ):
        """
        Initialize SCT generator.

        Args:
            provider: LLM provider to use ("openai" or "gemini").
            guideline: Optional clinical guideline to use ("american", "british", or "european").
        """
        self.provider = provider.lower()
        self.guideline = guideline

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

        # Load guideline if specified (use summary version to save tokens)
        self.guideline_content = None
        if guideline:
            # Try to load the summary version first (much shorter, saves tokens)
            guideline_summary_path = prompts_dir / f"{guideline}_guideline_summary.xml"
            guideline_full_path = prompts_dir / f"{guideline}_guideline.xml"

            if guideline_summary_path.exists():
                guideline_path = guideline_summary_path
                logger.info(f"Using summary version of {guideline} guideline")
            elif guideline_full_path.exists():
                guideline_path = guideline_full_path
                logger.warning(
                    f"Using full {guideline} guideline - this consumes many tokens. "
                    f"Consider creating a summary version at: {guideline_summary_path.name}"
                )
            else:
                raise FileNotFoundError(
                    f"Guideline not found: {guideline_path}. "
                    f"Available guidelines: american, british, european"
                )

            with open(guideline_path, "r", encoding="utf-8") as f:
                self.guideline_content = f.read()

            logger.info(
                f"Loaded {guideline} guideline ({len(self.guideline_content)} chars)"
            )

        logger.info(
            f"SCT Generator initialized with provider: {self.provider}"
            + (f", guideline: {guideline}" if guideline else "")
        )

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
            Rendered prompt string, optionally combined with guideline content.
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

        # Add guideline info if available
        if self.guideline:
            parameters.append(
                f"<guideline_source>{self.guideline.capitalize()} Clinical Guidelines</guideline_source>"
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

        # Combine with guideline if available
        if self.guideline_content:
            # Add guideline context before the main prompt
            combined_prompt = f"""<clinical_guideline_context>
The following clinical guideline should inform the generation of realistic, guideline-based scenarios:

{self.guideline_content}

Use this guideline as reference to ensure clinical accuracy and reflect real-world practice patterns.
</clinical_guideline_context>

{rendered}"""
            logger.debug(f"Combined prompt with {self.guideline} guideline")
            return combined_prompt

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
        guideline_info = f" with {self.guideline} guideline" if self.guideline else ""
        logger.info(
            f"Starting SCT item generation with {self.provider}{guideline_info}"
        )
        logger.info(f"Parameters - model: {model}, topic: {topic}, domain: {domain}")

        # Render prompt
        prompt = self._render_prompt(topic, domain, difficulty, additional_context)

        # Generate using structured outputs
        instructions = (
            "Generate a complete SCT item in English about hepatology "
            "following EXACTLY the format and quality criteria provided. "
            "Ensure all fields meet the quality specifications. "
            "CRITICAL REQUIREMENTS: "
            "1. The 'options' field MUST be exactly ['+2', '+1', '0', '-1', '-2'] - DO NOT modify these fixed scale values. "
            "2. The 'vignette' MUST be 120-240 words (aim for 150-200 words for optimal depth). COUNT CAREFULLY."
        )

        try:
            sct_item = self.client.parse_simple(
                input_text=prompt,
                model_class=SCTItem,
                model=model,
                instructions=instructions,
            )

            # Set the guideline field if a guideline was used
            if self.guideline:
                sct_item.guideline = self.guideline

            logger.info(f"SCT item generated successfully - domain: {sct_item.domain}")
            if sct_item.guideline:
                logger.info(f"  Guideline: {sct_item.guideline}")
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
    guideline: Optional[GuidelineType] = None,
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
        guideline: Optional clinical guideline ("american", "british", or "european").
        topic: Specific topic for the SCT item.
        domain: Clinical domain.
        difficulty: Difficulty level.
        additional_context: Additional context.

    Returns:
        Generated SCTItem.
    """
    generator = SCTGenerator(provider=provider, guideline=guideline)
    return generator.generate(model, topic, domain, difficulty, additional_context)


def generate_multiple_items(
    model: str,
    num_items: int,
    provider: str = "openai",
    guideline: Optional[GuidelineType] = None,
    topic: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> list[SCTItem]:
    """
    Generate multiple SCT items with the same configuration.

    Args:
        model: LLM model to use (must support structured outputs).
        num_items: Number of items to generate.
        provider: LLM provider to use ("openai" or "gemini").
        guideline: Optional clinical guideline ("american", "british", or "european").
        topic: Specific topic for the SCT item.
        domain: Clinical domain.
        difficulty: Difficulty level.
        additional_context: Additional context.

    Returns:
        List of generated SCTItems.
    """
    logger.info(f"Generating {num_items} SCT items...")

    generator = SCTGenerator(provider=provider, guideline=guideline)
    items = []

    for i in range(num_items):
        logger.info(f"Generating item {i + 1}/{num_items}...")
        try:
            item = generator.generate(
                model, topic, domain, difficulty, additional_context
            )
            items.append(item)
            logger.info(f"✓ Item {i + 1}/{num_items} completed")
        except Exception as e:
            logger.error(f"✗ Failed to generate item {i + 1}/{num_items}: {e}")
            # Continue with next item instead of failing completely
            continue

    logger.info(f"Successfully generated {len(items)}/{num_items} items")
    return items


def generate_items_per_guideline(
    model: str,
    items_per_guideline: int,
    provider: str = "openai",
    topic: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> dict[str, list[SCTItem]]:
    """
    Generate SCT items for each guideline (american, british, european).

    Args:
        model: LLM model to use (must support structured outputs).
        items_per_guideline: Number of items to generate per guideline.
        provider: LLM provider to use ("openai" or "gemini").
        topic: Specific topic for the SCT item.
        domain: Clinical domain.
        difficulty: Difficulty level.
        additional_context: Additional context.

    Returns:
        Dictionary mapping guideline names to lists of generated SCTItems.
        Example: {"american": [item1, item2], "british": [item3, item4], ...}
    """
    guidelines: list[GuidelineType] = ["american", "british", "european"]
    results = {}

    logger.info(
        f"Generating {items_per_guideline} items per guideline "
        f"(total: {items_per_guideline * len(guidelines)} items)"
    )

    for guideline in guidelines:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting generation for {guideline.upper()} guideline")
        logger.info(f"{'=' * 60}\n")

        items = generate_multiple_items(
            model=model,
            num_items=items_per_guideline,
            provider=provider,
            guideline=guideline,
            topic=topic,
            domain=domain,
            difficulty=difficulty,
            additional_context=additional_context,
        )

        results[guideline] = items
        logger.info(
            f"\n✓ Completed {guideline} guideline: "
            f"{len(items)}/{items_per_guideline} items generated\n"
        )

    # Summary
    total_generated = sum(len(items) for items in results.values())
    total_expected = items_per_guideline * len(guidelines)

    logger.info(f"\n{'=' * 60}")
    logger.info("GENERATION SUMMARY")
    logger.info(f"{'=' * 60}")
    for guideline, items in results.items():
        logger.info(f"  {guideline.capitalize()}: {len(items)} items")
    logger.info(f"  TOTAL: {total_generated}/{total_expected} items")
    logger.info(f"{'=' * 60}\n")

    return results
