"""Utility functions for exporting SCT items to different formats."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..logging import get_logger
from ..schemas import SCTItem

logger = get_logger(__name__)


def export_to_csv(output_path: Path, items: List[SCTItem]) -> None:
    """
    Export SCT items to CSV format.

    Args:
        output_path: Path where the CSV file should be saved.
        items: List of SCTItem objects to export.
    """
    if not items:
        logger.warning("No items to export to CSV")
        return

    logger.info(f"Exporting {len(items)} items to CSV: {output_path}")

    # Define CSV columns
    fieldnames = [
        "domain",
        "guideline",
        "vignette",
        "hypothesis",
        "new_information",
        "question",
        "options",  # Will be joined as string
        "author_notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            # Convert options list to string
            options_str = ", ".join(item.options)

            row = {
                "domain": item.domain,
                "guideline": item.guideline or "",
                "vignette": item.vignette,
                "hypothesis": item.hypothesis,
                "new_information": item.new_information,
                "question": item.question,
                "options": options_str,
                "author_notes": item.author_notes,
            }
            writer.writerow(row)

    logger.info(f"✓ CSV export complete: {output_path}")


def load_all_generated_items(generated_dir: Path) -> List[SCTItem]:
    """
    Load all JSON files from the generated directory.

    Args:
        generated_dir: Path to the directory containing generated JSON files.

    Returns:
        List of SCTItem objects loaded from JSON files.
    """
    if not generated_dir.exists():
        logger.warning(f"Generated directory does not exist: {generated_dir}")
        return []

    json_files = list(generated_dir.glob("sct_*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {generated_dir}")

    items = []
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Remove validation metadata if present
            if "_validation" in data:
                del data["_validation"]

            item = SCTItem(**data)
            items.append(item)

        except Exception as e:
            logger.error(f"Failed to load {json_file.name}: {e}")
            continue

    logger.info(f"Successfully loaded {len(items)} items from JSON files")
    return items


def export_generated_items_to_csv(
    generated_dir: Path, output_dir: Path, filename: str = None
) -> Path:
    """
    Load all generated items and export them to a CSV file.

    Args:
        generated_dir: Path to directory with generated JSON files.
        output_dir: Path to directory where CSV should be saved.
        filename: Optional custom filename. If None, generates timestamped name.

    Returns:
        Path to the created CSV file.
    """
    # Load all items
    items = load_all_generated_items(generated_dir)

    if not items:
        logger.warning("No items found to export")
        return None

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sct_items_{timestamp}.csv"

    output_path = output_dir / filename

    # Export to CSV
    export_to_csv(output_path, items)

    return output_path

