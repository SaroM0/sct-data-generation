"""Validators for SCT items."""

import re
from typing import List

from ..logging import get_logger
from ..schemas.sct_schemas import SCTItem
from ..schemas.validator_schemas import ValidationResult

logger = get_logger(__name__)


class SCTValidator:
    """Validator for SCT (Script Concordance Test) items."""

    # Valid options
    VALID_OPTIONS = ["+2", "+1", "0", "-1", "-2"]

    # Valid domains (regex pattern)
    DOMAIN_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,40}$")

    def __init__(self):
        """Initialize the validator."""
        logger.debug("SCT Validator initialized")

    def validate(self, item: SCTItem) -> ValidationResult:
        """
        Validate a complete SCT item.

        Args:
            item: SCTItem object to validate.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult(is_valid=True)

        logger.info(f"Validating SCT item - domain: {item.domain}")

        # Validate each field
        self._validate_domain(item.domain, result)
        self._validate_vignette(item.vignette, result)
        self._validate_hypothesis(item.hypothesis, result)
        self._validate_new_information(item.new_information, item.vignette, result)
        self._validate_question(item.question, result)
        self._validate_options(item.options, result)
        self._validate_author_notes(item.author_notes, result)

        # Log results
        if result.is_valid:
            logger.info(f"✓ Validation passed (warnings: {len(result.warnings)})")
        else:
            logger.error(f"✗ Validation failed with {len(result.errors)} error(s)")

        for error in result.errors:
            logger.error(f"  ERROR: {error}")
        for warning in result.warnings:
            logger.warning(f"  WARNING: {warning}")

        return result

    def _validate_domain(self, domain: str, result: ValidationResult):
        """Validate domain field."""
        if not domain or not domain.strip():
            result.add_error("Domain is required and cannot be empty")
            return

        # Check format
        if not self.DOMAIN_PATTERN.match(domain):
            result.add_error(
                f"Domain '{domain}' format invalid. Must match: ^[A-Za-z0-9_]{{3,40}}$"
            )

        # Check length
        if len(domain) < 3 or len(domain) > 40:
            result.add_error(
                f"Domain length must be between 3-40 characters (got {len(domain)})"
            )

    def _validate_vignette(self, vignette: str, result: ValidationResult):
        """Validate vignette field."""
        if not vignette or not vignette.strip():
            result.add_error("Vignette is required and cannot be empty")
            return

        # Word count - updated to 120-240 words
        word_count = len(vignette.split())
        if word_count < 120:
            result.add_error(f"Vignette too short: {word_count} words (minimum: 120)")
        elif word_count > 240:
            result.add_error(f"Vignette too long: {word_count} words (maximum: 240)")

        # Check for single paragraph (no line breaks)
        if "\n" in vignette.strip():
            result.add_error("Vignette must be a single paragraph (no line breaks)")

    def _validate_hypothesis(self, hypothesis: str, result: ValidationResult):
        """Validate hypothesis field."""
        if not hypothesis or not hypothesis.strip():
            result.add_error("Hypothesis is required and cannot be empty")
            return

        # Word count
        word_count = len(hypothesis.split())
        if word_count < 8:
            result.add_error(f"Hypothesis too short: {word_count} words (minimum: 8)")
        elif word_count > 25:
            result.add_error(f"Hypothesis too long: {word_count} words (maximum: 25)")

        # Check for question format
        if hypothesis.strip().endswith("?"):
            result.add_error(
                "Hypothesis must be an affirmative statement, not a question"
            )

    def _validate_new_information(
        self, new_info: str, vignette: str, result: ValidationResult
    ):
        """Validate new_information field."""
        if not new_info or not new_info.strip():
            result.add_error("New information is required and cannot be empty")
            return

        # Word count
        word_count = len(new_info.split())
        if word_count < 8:
            result.add_error(
                f"New information too short: {word_count} words (minimum: 8)"
            )
        elif word_count > 30:
            result.add_error(
                f"New information too long: {word_count} words (maximum: 30)"
            )

        # Check for question format
        if "?" in new_info:
            result.add_error("New information must be declarative, not a question")

        # Check for multiple sentences (max 2)
        sentence_count = len([s for s in re.split(r"[.!?]+", new_info) if s.strip()])
        if sentence_count > 2:
            result.add_error(
                f"New information has {sentence_count} sentences (maximum: 2)"
            )

    def _validate_question(self, question: str, result: ValidationResult):
        """Validate question field."""
        if not question or not question.strip():
            result.add_error("Question is required and cannot be empty")
            return

        # Check for extra spaces
        question_clean = question.strip()
        if question != question_clean:
            result.add_warning("Question has leading/trailing spaces")

    def _validate_options(self, options: List[str], result: ValidationResult):
        """Validate options field."""
        if not options:
            result.add_error("Options are required and cannot be empty")
            return

        # Check exact length
        if len(options) != 5:
            result.add_error(
                f"Options must have exactly 5 elements (got {len(options)})"
            )
            return

        # Check exact values and order
        if options != self.VALID_OPTIONS:
            result.add_error(
                f"Options must be exactly {self.VALID_OPTIONS} in that order (got {options})"
            )

        # Check for duplicates
        if len(options) != len(set(options)):
            result.add_error("Options contain duplicates")

        # Check for extra spaces or embedded descriptors
        for i, opt in enumerate(options):
            if opt != opt.strip():
                result.add_error(f"Option {i} has extra spaces: '{opt}'")
            if len(opt) > 2:  # "+2" is 2 chars
                result.add_error(
                    f"Option {i} has embedded descriptor: '{opt}' (should be just '+2', '+1', etc.)"
                )

    def _validate_author_notes(self, author_notes: str, result: ValidationResult):
        """Validate author_notes field (optional)."""
        if not author_notes or not author_notes.strip():
            # Optional field, no error
            return

        # Check length
        if len(author_notes) > 300:
            result.add_error(
                f"Author notes too long: {len(author_notes)} characters (maximum: 300)"
            )

        # Check sentence count
        sentence_count = len(
            [s for s in re.split(r"[.!?]+", author_notes) if s.strip()]
        )
        if sentence_count > 3:
            result.add_error(
                f"Author notes has {sentence_count} sentences (maximum: 3)"
            )


def validate_sct_item(item: SCTItem) -> ValidationResult:
    """
    Convenience function to validate a single SCT item.

    Args:
        item: SCTItem object to validate.

    Returns:
        ValidationResult with errors and warnings.
    """
    validator = SCTValidator()
    return validator.validate(item)
