from app.repositories.memory_repository import (
    save,
    update_intent,
    get_history,
    get_last,
    delete_history,
)

def save_message(...):
    return save(...)

def update_message_intent(...):
    return update_intent(...)

def get_memory(...):
    return get_history(...)

...