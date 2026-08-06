"""
Bitey Workflows Package

Central workflow modules.
Each workflow handles business logic only.

The workflow router decides which module runs.
Bitey Core manages:
- customers
- conversations
- messages
- tickets
- notifications
"""


from . import (
    ai_assistant,
    camera_installation,
    computer_repair,
    default,
    hardware_upgrade,
    mobile_repair,
    network_support,
)