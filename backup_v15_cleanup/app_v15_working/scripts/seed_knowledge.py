"""
Seed initial BiteFixes knowledge base.
"""

from datetime import datetime, timezone

from app.database.supabase import supabase


COMPANY_ID = 1


knowledge_items = [

    {
        "company_id": COMPANY_ID,
        "title": "Notebook lento",
        "category": "Hardware",
        "question": "Meu notebook esta lento",
        "answer": (
            "Podemos melhorar o desempenho do notebook "
            "com upgrade de SSD e memória RAM."
        ),
        "tags": [
            "notebook",
            "lento",
            "ssd",
            "ram",
            "memoria"
        ],
        "intent": "hardware_upgrade",
        "service_id": 7,
        "priority": "normal",
        "requires_ticket": True,
        "is_active": True,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    },


    {
        "company_id": COMPANY_ID,
        "title": "Manutenção computador",
        "category": "Hardware",
        "question": "Meu computador não funciona",
        "answer": (
            "Podemos realizar diagnóstico "
            "e manutenção do equipamento."
        ),
        "tags": [
            "computador",
            "pc",
            "conserto"
        ],
        "intent": "computer_repair",
        "service_id": 8,
        "priority": "normal",
        "requires_ticket": True,
        "is_active": True,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

]


def seed():

    print("Creating knowledge base...")


    result = (
        supabase
        .table("knowledge_base")
        .insert(
            knowledge_items
        )
        .execute()
    )


    print(result.data)

    print("KNOWLEDGE SEED COMPLETE")


if __name__ == "__main__":
    seed()