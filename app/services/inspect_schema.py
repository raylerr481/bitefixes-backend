from app.database.supabase import supabase

tables = [
    "customers",
    "conversations",
    "messages",
    "tickets",
    "services",
    "customer_devices"
]

for table in tables:
    print("\n" + "=" * 60)
    print(table.upper())

    try:
        r = (
            supabase
            .table(table)
            .select("*")
            .limit(1)
            .execute()
        )

        if r.data:
            print(r.data[0].keys())
        else:
            print("TABLE EMPTY")

    except Exception as e:
        print(e)