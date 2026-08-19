"""Governed information requirements for conversational Bitey workflows."""
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core.channel_preferences import available_contact_channels


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
    "preferred_contact_channel": "canal preferido",
}


def evaluate_information_needs(*, intent: str | None = None, workflow: str | None = None,
                               current_data: dict[str, Any] | None = None,
                               requires_contact: bool = False) -> list[InformationRequirement]:
    """Return the smallest useful set of information for the current step."""
    data = current_data or {}
    requirements: list[InformationRequirement] = []

    technical = {"mobile_repair", "screen_repair", "computer_repair", "hardware_upgrade"}
    if intent in technical or workflow in technical:
        if not data.get("device_model"):
            requirements.append(InformationRequirement(
                "device_model", RequirementPriority.IMPORTANT,
                "brand/model changes diagnosis and available solution",
                "¿Qué marca y modelo es el equipo?",
            ))

    if requires_contact:
        if not data.get("name"):
            requirements.append(InformationRequirement(
                "name", RequirementPriority.IMPORTANT,
                "needed to personalize and identify the request",
                "¿Cómo te llamas?",
            ))
        if not data.get("last_name"):
            requirements.append(InformationRequirement(
                "last_name", RequirementPriority.OPTIONAL,
                "helps identify the customer when needed",
                "¿Cuál es tu apellido?",
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
        if data.get("phone") and not data.get("preferred_contact_channel"):
            requirements.append(InformationRequirement(
                "preferred_contact_channel", RequirementPriority.IMPORTANT,
                "lets the customer choose how the conversation continues",
                "¿Prefieres continuar por WhatsApp o por este chat de la web?",
            ))

    return requirements


def contact_channel_options(current_data: dict[str, Any] | None = None) -> list[dict[str, str]]:
    data = current_data or {}
    return [{"channel": option.channel.value, "prompt": option.prompt, "reason": option.reason}
            for option in available_contact_channels(has_phone=bool(data.get("phone")), has_email=bool(data.get("email")))]


def next_information_requirement(requirements: list[InformationRequirement]) -> InformationRequirement | None:
    """Choose one question at a time, prioritizing the smallest next action."""
    order = {RequirementPriority.REQUIRED: 0, RequirementPriority.IMPORTANT: 1,
             RequirementPriority.OPTIONAL: 2, RequirementPriority.NOT_NEEDED: 3}
    candidates = [r for r in requirements if r.priority != RequirementPriority.NOT_NEEDED]
    return sorted(candidates, key=lambda r: order[r.priority])[0] if candidates else None
