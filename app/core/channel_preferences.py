"""Channel-neutral communication preferences shared by all Bitey channels."""
from dataclasses import dataclass
from enum import Enum


class ContactChannel(str, Enum):
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"


@dataclass(frozen=True)
class ChannelPreference:
    channel: ContactChannel
    prompt: str
    reason: str


def available_contact_channels(*, has_phone: bool = False, has_email: bool = False) -> list[ChannelPreference]:
    options = [ChannelPreference(ContactChannel.WEBSITE, "¿Prefieres continuar por este chat de la web?", "keep the conversation in the current channel")]
    if has_phone:
        options.extend([
            ChannelPreference(ContactChannel.WHATSAPP, "¿Prefieres continuar por WhatsApp?", "continue through the user's phone"),
            ChannelPreference(ContactChannel.MESSENGER, "¿Prefieres continuar por Messenger?", "continue through Facebook Messenger"),
            ChannelPreference(ContactChannel.TELEGRAM, "¿Prefieres continuar por Telegram?", "continue through Telegram"),
            ChannelPreference(ContactChannel.SMS, "¿Prefieres continuar por SMS?", "continue through text messaging"),
            ChannelPreference(ContactChannel.PHONE, "¿Prefieres que te llamemos?", "continue by phone call"),
        ])
    if has_email:
        options.append(ChannelPreference(ContactChannel.EMAIL, "¿Prefieres continuar por correo electrónico?", "use asynchronous email communication"))
    return options


def normalize_contact_channel(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower().replace("_", "-")
    aliases = {
        "web": "website", "webchat": "website", "site": "website",
        "wa": "whatsapp", "whatsapp-business": "whatsapp",
        "facebook": "messenger", "fb-messenger": "messenger",
        "telegram-bot": "telegram", "mail": "email", "e-mail": "email",
    }
    value = aliases.get(value, value)
    return value if value in {item.value for item in ContactChannel} else None
