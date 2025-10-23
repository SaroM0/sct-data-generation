"""Utility functions for validator module."""

import json
from datetime import datetime
from pathlib import Path

from ..logging import get_logger
from ..schemas.sct_schemas import SCTItem
from ..schemas.validator_schemas import ValidationResult

logger = get_logger(__name__)


def _save_sct_to_folder(
    item: SCTItem,
    folder: str,
    include_validation: bool = False,
    validation_result: ValidationResult = None,
) -> str:
    """
    Internal function to save an SCT item to a specific folder.

    Args:
        item: SCTItem object to save.
        folder: Target folder path.
        include_validation: Whether to include validation metadata.
        validation_result: ValidationResult to include if include_validation is True.

    Returns:
        Path to the saved file.
    """
    # Create output directory if it doesn't exist
    output_folder = Path(folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp and domain
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    domain_clean = item.domain.lower().replace("_", "-")
    filename = f"sct_{domain_clean}_{timestamp}.json"

    # Full file path
    file_path = output_folder / filename

    # Prepare data to save
    item_data = item.model_dump()

    # Add validation metadata if requested
    if include_validation and validation_result:
        item_data["_validation"] = {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "validated_at": datetime.now().isoformat(),
        }

    # Save to JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(item_data, f, ensure_ascii=False, indent=2)

    return str(file_path)


def save_validated_sct(
    item: SCTItem,
    validation_result: ValidationResult,
    base_output_dir: str = "data",
) -> dict:
    """
    Save an SCT item to all appropriate folders based on validation result.

    Always saves to:
    - data/generated/ (all items)
    - data/validated/ (if validation passed) OR data/validation_failed/ (if failed)

    Args:
        item: SCTItem object to save.
        validation_result: ValidationResult from validation.
        base_output_dir: Base output directory. Defaults to "data".

    Returns:
        Dictionary with paths: {'generated': path, 'validated': path or None, 'failed': path or None}
    """
    base_path = Path(base_output_dir)
    paths = {}

    # Always save to generated folder (without validation metadata)
    generated_path = _save_sct_to_folder(
        item, str(base_path / "generated"), include_validation=False
    )
    paths["generated"] = generated_path
    logger.info(f"SCT item saved to generated: {generated_path}")

    # Save to validated or validation_failed folder (with validation metadata)
    if validation_result.is_valid:
        validated_path = _save_sct_to_folder(
            item,
            str(base_path / "validated"),
            include_validation=True,
            validation_result=validation_result,
        )
        paths["validated"] = validated_path
        paths["failed"] = None
        logger.info(f"SCT item saved to validated: {validated_path}")
    else:
        failed_path = _save_sct_to_folder(
            item,
            str(base_path / "validation_failed"),
            include_validation=True,
            validation_result=validation_result,
        )
        paths["validated"] = None
        paths["failed"] = failed_path
        logger.info(f"SCT item saved to validation_failed: {failed_path}")

    return paths
