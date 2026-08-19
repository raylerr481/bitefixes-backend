"""Channel preference policy shared by web chat and WhatsApp."""
from dataclasses import dataclass
from enum import Enum


class ContactChannel(str, Enum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


@dataclass(frozen=True)
class ChannelPreference:
    channel: ContactChannel
    prompt: str
    reason: str


def available_contact_channels(*, has_phone: bool = False, has_email: bool = False) -> list[ChannelPreference]:
    options: list[ChannelPreference] = [
        ChannelPreference(ContactChannel.WEB, "¿Prefieres continuar por este chat de la web?", "keep the conversation in the current channel"),
    ]
    if has_phone:
        options.append(ChannelPreference(ContactChannel.WHATSAPP, "¿Prefieres continuar por WhatsApp?", "continue through the user's phone"))
    if has_email:
        options.append(ChannelPreference(ContactChannel.EMAIL, "¿Prefieres continuar por correo electrónico?", "use asynchronous email communication"))
    return options


def normalize_contact_channel(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower().replace("_", "-")
    aliases = {"webchat": "web", "website": "web", "wa": "whatsapp", "mail": "email"}
    value = aliases.get(value, value)
    return value if value in {item.value for item in ContactChannel} else None
