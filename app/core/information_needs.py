"""Governed information requirements for conversational Bitey workflows.

Bitey may request customer/business information only when it improves the
current decision or is required to continue a workflow. This module keeps
collection policy separate from the WordPress UI.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RequirementPriority(str, Enum):
    REQUIRED = "required"
    IMPORTANT = "important"
    OPTIONAL = "optional"
    NOT_NEEDED = "not_needed"


@dataclass(frozen=True)
class InformationRequirement:
    field: str
    priority: RequirementPriority
    reason: str
    prompt: str


PERSON_FIELDS = {
    "name": "nombre",
    "last_name": "apellido",
    "phone": "teléfono / WhatsApp",
    "email": "correo electrónico",
}


def evaluate_information_needs(
    *,
    intent: str | None = None,
    workflow: str | None = None,
    current_data: dict[str, Any] | None = None,
    requires_contact: bool = False,
) -> list[InformationRequirement]:
    """Return the smallest useful set of information for the current step."""
    data = current_data or {}
    requirements: list[InformationRequirement] = []

    # Identification is never mandatory merely because a chat started.
    if requires_contact:
        if not data.get("name"):
            requirements.append(InformationRequirement(
                "name", RequirementPriority.IMPORTANT,
                "needed to personalize and identify the request",
                "¿Cómo te llamas?",
            ))
        if not data.get("phone") and not data.get("email"):
            requirements.append(InformationRequirement(
                "phone", RequirementPriority.REQUIRED,
                "a contact channel is required to continue this request",
                "¿Prefieres dejarme tu teléfono o WhatsApp?",
            ))
            requirements.append(InformationRequirement(
                "email", RequirementPriority.OPTIONAL,
                "alternative contact channel",
                "También puedes dejarme tu correo electrónico si lo prefieres.",
            ))

    # Technical workflows first collect information that affects diagnosis.
    technical = {"mobile_repair", "screen_repair", "computer_repair", "hardware_upgrade"}
    if intent in technical or workflow in technical:
        if not data.get("device_model"):
            requirements.insert(0, InformationRequirement(
                "device_model", RequirementPriority.IMPORTANT,
                "brand/model changes diagnosis and available solution",
                "¿Qué marca y modelo es el equipo?",
            ))

    # Remove optional questions when a higher-value missing field exists.
    return requirements


def next_information_requirement(requirements: list[InformationRequirement]) -> InformationRequirement | None:
    """Choose one question at a time, prioritizing the smallest next action."""
    order = {
        RequirementPriority.REQUIRED: 0,
        RequirementPriority.IMPORTANT: 1,
        RequirementPriority.OPTIONAL: 2,
        RequirementPriority.NOT_NEEDED: 3,
    }
    candidates = [r for r in requirements if r.priority != RequirementPriority.NOT_NEEDED]
    return sorted(candidates, key=lambda r: order[r.priority])[0] if candidates else None
