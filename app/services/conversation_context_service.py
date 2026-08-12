"""
Compatibility layer for Bitey Core.

The conversation context functions are implemented in
conversation_service.py. This module preserves the
conversation_context_service import used by older Bitey versions.
"""

from app.services.conversation_service import (
    update_conversation_context,
)

