"""Schemas for SCT (Script Concordance Test) items."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class SCTQuestion(BaseModel):
    """
    Schema for a single SCT question within a clinical scenario.

    Follows the format: "If you were thinking of... and then you find that... this hypothesis/plan becomes..."
    """

    question_type: Literal["diagnosis", "management", "followup"] = Field(
        description="Type of clinical reasoning being assessed"
    )

    hypothesis: str = Field(
        description="The initial clinical thought/plan (8-25 words) - 'If you were thinking of...'"
    )

    new_information: str = Field(
        description="Additional clinical data that modulates the hypothesis (8-30 words) - 'and then you find that...'"
    )

    effect_phrase: str = Field(
        description="How the hypothesis/plan changes - 'this hypothesis/plan becomes...' or similar",
        default="this hypothesis becomes",
    )

    options: list[Literal["+2", "+1", "0", "-1", "-2"]] = Field(
        description="FIXED Likert scale options - MUST be exactly ['+2', '+1', '0', '-1', '-2'] in that order",
        default=["+2", "+1", "0", "-1", "-2"],
    )

    author_notes: str = Field(
        description="Brief clinical justification (max 3 sentences, max 300 characters)"
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


class SCTItem(BaseModel):
    """
    Schema for a complete SCT (Script Concordance Test) item.

    Used for generating structured clinical case scenarios with 3 evaluation scenarios:
    one focused on diagnosis, one on management, and one on follow-up.
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

    questions: list[SCTQuestion] = Field(
        description="Exactly 3 independent questions: one diagnosis, one management, one follow-up (in that order)",
        min_length=3,
        max_length=3,
    )

    @field_validator("questions")
    @classmethod
    def validate_question_types(cls, v):
        """Ensure exactly one question of each type in correct order."""
        if len(v) != 3:
            raise ValueError("Must have exactly 3 questions")

        expected_types = ["diagnosis", "management", "followup"]
        actual_types = [q.question_type for q in v]

        if actual_types != expected_types:
            raise ValueError(
                f"Questions must be in order: diagnosis, management, followup. "
                f"Got: {actual_types}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "Cirrhosis_Complications",
                "guideline": "american",
                "vignette": "A 58-year-old man with alcoholic cirrhosis Child-Pugh B presents to the emergency department with fever, abdominal pain...",
                "questions": [
                    {
                        "question_type": "diagnosis",
                        "hypothesis": "spontaneous bacterial peritonitis",
                        "new_information": "ascitic fluid PMN count is 320 cells/µL",
                        "effect_phrase": "this diagnosis becomes",
                        "options": ["+2", "+1", "0", "-1", "-2"],
                        "author_notes": "PMN ≥250 supports SBP diagnosis; should shift toward +2/+1...",
                    },
                    {
                        "question_type": "management",
                        "hypothesis": "starting empiric ceftriaxone",
                        "new_information": "patient has documented anaphylaxis to penicillins",
                        "effect_phrase": "this management becomes",
                        "options": ["+2", "+1", "0", "-1", "-2"],
                        "author_notes": "Penicillin allergy requires alternative; ceftriaxone less appropriate...",
                    },
                    {
                        "question_type": "followup",
                        "hypothesis": "scheduling a repeat paracentesis in 48 hours",
                        "new_information": "clinical improvement with resolution of fever",
                        "effect_phrase": "this plan becomes",
                        "options": ["+2", "+1", "0", "-1", "-2"],
                        "author_notes": "Clinical improvement suggests good response; repeat may be less necessary...",
                    },
                ],
            }
        }
