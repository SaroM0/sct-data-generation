"""Helper utilities for saving generated SCT items."""

import json
from datetime import datetime
from pathlib import Path

from ..logging import get_logger
from ..schemas import SCTItem

logger = get_logger(__name__)


def save_sct_item(
    item: SCTItem,
    output_dir: str = "data/generated",
) -> str:
    """
    Save a single SCT item to a JSON file.

    Each item is saved in a separate file with timestamp and domain.

    Args:
        item: SCTItem object to save.
        output_dir: Output directory path. Defaults to "data/generated".

    Returns:
        Path to the saved file.
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp and domain
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    domain_clean = item.domain.lower().replace("_", "-")
    filename = f"sct_{domain_clean}_{timestamp}.json"

    # Full file path
    file_path = output_path / filename

    # Convert item to dict
    item_data = item.model_dump()

    # Save to JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(item_data, f, ensure_ascii=False, indent=2)

    logger.info(f"SCT item saved to: {file_path}")

    return str(file_path)
