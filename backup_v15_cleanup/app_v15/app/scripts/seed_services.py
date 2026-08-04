"""
Seed initial BiteFixes services.

Creates:
- service categories
- services

Company:
BiteFixes (id=1)
"""


from app.database.supabase import supabase



COMPANY_ID = 1



# =====================================================
# SERVICE CATEGORIES
# =====================================================

categories = [

    {
        "company_id": COMPANY_ID,
        "name": "Hardware",
        "description": "Computer and notebook hardware services",
        "is_active": True
    },

    {
        "company_id": COMPANY_ID,
        "name": "Software",
        "description": "Operating system and software services",
        "is_active": True
    },

    {
        "company_id": COMPANY_ID,
        "name": "Network",
        "description": "Network installation and configuration",
        "is_active": True
    },

    {
        "company_id": COMPANY_ID,
        "name": "Security",
        "description": "CCTV and security systems",
        "is_active": True
    },

    {
        "company_id": COMPANY_ID,
        "name": "Support",
        "description": "Technical support services",
        "is_active": True
    }

]



def create_categories():

    created = []


    for category in categories:

        result = (
            supabase
            .table("service_categories")
            .insert(category)
            .execute()
        )


        if result.data:

            created.append(
                result.data[0]
            )


    return created



# =====================================================
# SERVICES
# =====================================================


def create_services(category_map):


    services = [

        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Hardware"],
            "name": "Notebook upgrade SSD and RAM",
            "description": "Upgrade hardware performance",
            "is_active": True
        },


        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Hardware"],
            "name": "Computer repair",
            "description": "Desktop and notebook repair",
            "is_active": True
        },


        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Software"],
            "name": "Windows installation",
            "description": "Operating system installation",
            "is_active": True
        },


        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Network"],
            "name": "Network configuration",
            "description": "LAN and WiFi configuration",
            "is_active": True
        },


        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Security"],
            "name": "CCTV installation",
            "description": "Security camera installation",
            "is_active": True
        },


        {
            "company_id": COMPANY_ID,
            "category_id": category_map["Support"],
            "name": "Remote technical support",
            "description": "Remote assistance",
            "is_active": True
        }

    ]


    result = (
        supabase
        .table("services")
        .insert(services)
        .execute()
    )


    return result.data



# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":


    print("Creating categories...")


    categories_created = create_categories()


    category_map = {

        item["name"]:
        item["id"]

        for item in categories_created

    }


    print(category_map)



    print("Creating services...")


    services_created = create_services(
        category_map
    )


    print(
        services_created
    )


    print(
        "SEED COMPLETE"
    )