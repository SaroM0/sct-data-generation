"""Schemas for SCT (Script Concordance Test) items."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class SCTItem(BaseModel):
    """
    Schema for a complete SCT (Script Concordance Test) item.

    Used for generating structured clinical case scenarios for hepatology assessment.
    """

    domain: str = Field(
        description="Clinical subdomain category (e.g., Cirrhosis_Complications, Biliary_Cholangitis)"
    )

    guideline: Optional[Literal["american", "british", "european"]] = Field(
        default=None,
        description="Clinical guideline used as reference for this item (american, british, or european)",
    )

    vignette: str = Field(
        description="Brief clinical case (120-240 words) establishing context and reasonable uncertainty"
    )

    hypothesis: str = Field(
        description="Single, clear proposition to evaluate (diagnostic, test utility, or management)"
    )

    new_information: str = Field(
        description="Additional data that modulates the hypothesis (result, imaging, evolution)"
    )

    question: str = Field(
        description="Standard SCT question about probability change of the hypothesis"
    )

    options: list[Literal["+2", "+1", "0", "-1", "-2"]] = Field(
        description="FIXED Likert scale options - MUST be exactly ['+2', '+1', '0', '-1', '-2'] in that order. DO NOT change these values.",
        default=["+2", "+1", "0", "-1", "-2"],
    )

    author_notes: str = Field(
        description="Brief clinical justification for the writer (not shown to panel)"
    )

    @field_validator("options")
    @classmethod
    def validate_options_fixed(cls, v):
        """Ensure options are exactly the required fixed values."""
        expected = ["+2", "+1", "0", "-1", "-2"]
        if v != expected:
            raise ValueError(
                f"Options must be exactly {expected} in that order. "
                f"Got: {v}. These are FIXED scale values and cannot be changed."
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "Cirrhosis_Complications",
                "guideline": "american",
                "vignette": "Varón de 58 años con cirrosis alcohólica Child-Pugh B...",
                "hypothesis": "El cuadro es compatible con peritonitis bacteriana espontánea (PBE).",
                "new_information": "Recuento de PMN en líquido ascítico de 320 células/µL",
                "question": "¿Cómo cambia la probabilidad de la hipótesis?",
                "options": ["+2", "+1", "0", "-1", "-2"],
                "author_notes": "PMN ≥250 respalda PBE; debería desplazar hacia +2/+1...",
            }
        }
