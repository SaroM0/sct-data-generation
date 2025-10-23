"""SCT Data Generation package."""

from .logging import setup_logging

# Initialize logging when package is imported
setup_logging()

__version__ = "0.1.0"

# Export main components
from .generator import SCTGenerator, generate_sct_item, save_sct_item
from .schemas import SCTItem
from .validators import ValidationResult, validate_sct_item

__all__ = [
    "SCTGenerator",
    "generate_sct_item",
    "save_sct_item",
    "SCTItem",
    "setup_logging",
    "validate_sct_item",
    "ValidationResult",
]
