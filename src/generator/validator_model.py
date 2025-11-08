"""Model-based SCT Item Validator using LLM with different guideline."""

import random
from pathlib import Path
from typing import Literal, Optional

from ..llm.gemini import GeminiClient
from ..llm.openai import OpenAIClient
from ..logging import get_logger
from ..schemas.sct_schemas import SCTItem, SCTValidatorResult

logger = get_logger(__name__)

# Type for guideline selection
GuidelineType = Literal["american", "british", "european"]


class SCTModelValidator:
    """
    Model-based validator for SCT items.
    
    Uses an LLM model with a DIFFERENT clinical guideline than the one used
    for item creation to validate the item and provide baseline responses.
    """

    def __init__(self, provider: str = "openai"):
        """
        Initialize SCT model validator.

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

        # Load validator prompt template
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.validator_prompt_path = prompts_dir / "sct_validator_prompt.xml"

        if not self.validator_prompt_path.exists():
            raise FileNotFoundError(
                f"Validator prompt template not found: {self.validator_prompt_path}"
            )

        # Load the XML template
        with open(self.validator_prompt_path, "r", encoding="utf-8") as f:
            self.validator_template = f.read()

        logger.info(
            f"SCT Model Validator initialized with provider: {self.provider}"
        )

    def _select_validator_guideline(
        self, creation_guideline: Optional[GuidelineType]
    ) -> GuidelineType:
        """
        Select a validator guideline different from the creation guideline.

        Args:
            creation_guideline: Guideline used to create the item (can be None).

        Returns:
            A guideline different from creation_guideline.
        """
        all_guidelines: list[GuidelineType] = ["american", "british", "european"]

        if creation_guideline is None:
            # If no creation guideline, randomly select one
            return random.choice(all_guidelines)

        # Select a different guideline
        available = [g for g in all_guidelines if g != creation_guideline]
        if not available:
            # Fallback: if somehow all are the same, just pick randomly
            logger.warning(
                f"Could not find different guideline from {creation_guideline}, "
                "selecting randomly"
            )
            return random.choice(all_guidelines)

        return random.choice(available)

    def _load_validator_guideline(self, guideline: GuidelineType) -> str:
        """
        Load the content of a clinical guideline.

        Args:
            guideline: Guideline to load ("american", "british", or "european").

        Returns:
            Guideline content as string.
        """
        prompts_dir = Path(__file__).parent.parent / "prompts"

        # Try to load the summary version first (much shorter, saves tokens)
        guideline_summary_path = prompts_dir / f"{guideline}_guideline_summary.xml"
        guideline_full_path = prompts_dir / f"{guideline}_guideline.xml"

        if guideline_summary_path.exists():
            guideline_path = guideline_summary_path
            logger.debug(f"Using summary version of {guideline} guideline for validation")
        elif guideline_full_path.exists():
            guideline_path = guideline_full_path
            logger.debug(
                f"Using full {guideline} guideline for validation - "
                "this consumes many tokens"
            )
        else:
            raise FileNotFoundError(
                f"Guideline not found: {guideline}. "
                f"Available guidelines: american, british, european"
            )

        with open(guideline_path, "r", encoding="utf-8") as f:
            guideline_content = f.read()

        logger.debug(
            f"Loaded {guideline} guideline for validation "
            f"({len(guideline_content)} chars)"
        )
        return guideline_content

    def _render_validator_prompt(
        self, item: SCTItem, validator_guideline: GuidelineType
    ) -> str:
        """
        Render the validator prompt from XML template.

        Args:
            item: SCTItem to validate.
            validator_guideline: Guideline to use for validation.

        Returns:
            Rendered prompt string.
        """
        # Load validator guideline content
        validator_guideline_content = self._load_validator_guideline(
            validator_guideline
        )

        # Build questions XML
        questions_xml = ""
        for question in item.questions:
            options_str = ", ".join(question.options)
            questions_xml += f"""      <question>
        <question_type>{question.question_type}</question_type>
        <hypothesis>{question.hypothesis}</hypothesis>
        <new_information>{question.new_information}</new_information>
        <effect_phrase>{question.effect_phrase}</effect_phrase>
        <options>[{options_str}]</options>
        <author_notes>{question.author_notes}</author_notes>
      </question>
"""

        # Handle optional author_notes
        if item.author_notes:
            author_notes_section = f"    <author_notes>{item.author_notes}</author_notes>"
        else:
            author_notes_section = ""

        # Replace placeholders in template
        prompt = self.validator_template
        prompt = prompt.replace("{{CREATION_GUIDELINE}}", item.guideline or "none")
        prompt = prompt.replace("{{VALIDATOR_GUIDELINE}}", validator_guideline)
        prompt = prompt.replace("{{DOMAIN}}", item.domain)
        prompt = prompt.replace("{{VIGNETTE}}", item.vignette)
        prompt = prompt.replace("{{AUTHOR_NOTES_SECTION}}", author_notes_section)
        prompt = prompt.replace("{{QUESTIONS_SECTION}}", questions_xml.strip())
        prompt = prompt.replace("{{VALIDATOR_GUIDELINE_CONTENT}}", validator_guideline_content)

        return prompt

    def validate(
        self, item: SCTItem, model: str
    ) -> SCTValidatorResult:
        """
        Validate an SCT item using a different guideline.

        Args:
            item: SCTItem to validate.
            model: LLM model to use (must support structured outputs).

        Returns:
            SCTValidatorResult with validation responses and notes.

        Raises:
            ValueError: If model refuses the request or validation fails.
        """
        # Select a different guideline
        validator_guideline = self._select_validator_guideline(item.guideline)

        logger.info(
            f"Validating SCT item (creation guideline: {item.guideline or 'none'}, "
            f"validator guideline: {validator_guideline})"
        )

        # Render validator prompt
        prompt = self._render_validator_prompt(item, validator_guideline)

        # Generate validation using structured outputs
        instructions = (
            "You are validating an SCT item using a DIFFERENT clinical guideline "
            "than the one used for creation. "
            "Select the most appropriate response option (+2, +1, 0, -1, or -2) "
            "for each of the 3 questions based on how the new information affects "
            "the hypothesis/plan according to your guideline perspective. "
            "Provide overall validation notes explaining your assessment. "
            "CRITICAL: The validator_guideline field MUST be different from the "
            "creation guideline."
        )

        try:
            validator_result = self.client.parse_simple(
                input_text=prompt,
                model_class=SCTValidatorResult,
                model=model,
                instructions=instructions,
            )

            # Verify that validator guideline is different from creation guideline
            if validator_result.validator_guideline == item.guideline:
                logger.warning(
                    f"Validator guideline ({validator_result.validator_guideline}) "
                    f"matches creation guideline ({item.guideline}). "
                    "This should not happen."
                )

            logger.info(
                f"✓ Validation completed with {validator_result.validator_guideline} guideline"
            )
            logger.debug(
                f"Validator responses: "
                f"{[r.selected_option for r in validator_result.validator_responses]}"
            )

            return validator_result

        except ValueError as e:
            logger.error(f"Model refused validation request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error validating SCT item: {e}")
            raise


def validate_sct_item_with_model(
    item: SCTItem, model: str, provider: str = "openai"
) -> SCTValidatorResult:
    """
    Convenience function to validate an SCT item using a model with different guideline.

    Args:
        item: SCTItem to validate.
        model: LLM model to use (must support structured outputs).
        provider: LLM provider to use ("openai" or "gemini").

    Returns:
        SCTValidatorResult with validation responses and notes.
    """
    validator = SCTModelValidator(provider=provider)
    return validator.validate(item, model)

