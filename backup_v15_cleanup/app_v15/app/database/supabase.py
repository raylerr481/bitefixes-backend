"""
BiteFixes Supabase Database Layer

Central database connection manager.

Architecture:

Services
    |
    v
SupabaseManager
    |
    v
Supabase Client
    |
    v
PostgreSQL Database
"""


from supabase import create_client, Client

from app.config import settings


class SupabaseManager:
    """
    Central manager for Supabase connection.
    """


    def __init__(self):

        self.client: Client | None = None

        self.connect()



    # =====================================================
    # CREATE CONNECTION
    # =====================================================

    def connect(self):

        try:

            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )


            print(
                "✅ Supabase conectado correctamente"
            )


            return self.client


        except Exception as error:


            print(
                "❌ Error conectando Supabase:",
                error
            )


            self.client = None


            return None



    # =====================================================
    # GET CLIENT
    # =====================================================

    def get_client(self):


        if self.client is None:

            self.connect()


        return self.client



    # =====================================================
    # HEALTH CHECK
    # =====================================================

    def check_connection(self):

        try:


            if self.client is None:

                return False



            response = (
                self.client
                .table("customers")
                .select("id")
                .limit(1)
                .execute()
            )


            return True



        except Exception as error:


            print(
                "❌ Supabase health check error:",
                error
            )


            return False



    # =====================================================
    # GENERIC TABLE ACCESS
    # =====================================================

    def table(self, table_name: str):

        if self.client is None:

            self.connect()


        return self.client.table(table_name)



# =====================================================
# SINGLETON INSTANCE
# =====================================================

supabase_manager = SupabaseManager()



# =====================================================
# DIRECT CLIENT ACCESS
# =====================================================

supabase = supabase_manager.get_client()



# =====================================================
# LEGACY COMPATIBILITY
#
# Older services use:
#
# from app.database.supabase import database
#
# Keep this to avoid breaking modules.
# =====================================================

database = supabase_manager