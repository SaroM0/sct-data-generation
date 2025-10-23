"""Validation schemas for SCT items."""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class SCTDomain(str, Enum):
    """Valid SCT clinical domains."""

    CIRRHOSIS_COMPLICATIONS = "Cirrhosis_Complications"
    BILIARY_CHOLANGITIS = "Biliary_Cholangitis"
    VIRAL_AUTOIMMUNE_TOXIC = "Viral_Autoimmune_Toxic"
    FATTY_LIVER_NASH = "Fatty_Liver_NASH"
    MASSES_HCC_SURVEILLANCE = "Masses_HCC_Surveillance"
    TRANSPLANT_PRETR = "Transplant_Pretr"


class ValidationResult(BaseModel):
    """Result of SCT item validation."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
