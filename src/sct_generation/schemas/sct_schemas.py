"""Schemas for SCT (Script Concordance Test) items."""

from pydantic import BaseModel, Field


class SCTItem(BaseModel):
    """
    Schema for a complete SCT (Script Concordance Test) item.

    Used for generating structured clinical case scenarios for hepatology assessment.
    """

    domain: str = Field(
        description="Clinical subdomain category (e.g., Cirrhosis_Complications, Biliary_Cholangitis)"
    )

    vignette: str = Field(
        description="Brief clinical case (70-120 words) establishing context and reasonable uncertainty"
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

    options: list[str] = Field(
        description="Likert scale options for response",
        default=["+2", "+1", "0", "-1", "-2"],
    )

    author_notes: str = Field(
        description="Brief clinical justification for the writer (not shown to panel)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "Cirrhosis_Complications",
                "vignette": "Varón de 58 años con cirrosis alcohólica Child-Pugh B...",
                "hypothesis": "El cuadro es compatible con peritonitis bacteriana espontánea (PBE).",
                "new_information": "Recuento de PMN en líquido ascítico de 320 células/µL",
                "question": "¿Cómo cambia la probabilidad de la hipótesis?",
                "options": ["+2", "+1", "0", "-1", "-2"],
                "author_notes": "PMN ≥250 respalda PBE; debería desplazar hacia +2/+1...",
            }
        }
