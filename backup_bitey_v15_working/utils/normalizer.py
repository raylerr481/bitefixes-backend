"""
Bitey Text Normalizer.

Shared utility for AI services.
"""

import unicodedata
import re


def normalize_text(text: str) -> str:
    """
    Normalize text for AI matching.
    """

    if not text:
        return ""


    text = text.lower()


    text = unicodedata.normalize(
        "NFD",
        text
    )


    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )


    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()



def normalizar_texto(text: str) -> str:
    """
    Compatibility alias.

    Keeps old Bitey modules working.
    """

    return normalize_text(text)