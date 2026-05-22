from app.schemas.user import UserCreate
from app.services.db import (
    db_get_user,
    db_user_exists,
    db_create_user,
    db_update_user_subscription,
)


class AuthService:
    @staticmethod
    def signup(email: str, password: str):
        from app.database import supabase
        try:
            return supabase.auth.sign_up({"email": email, "password": password})
        except Exception as e:
            raise Exception(f"Signup error: {e}")

    @staticmethod
    def login(email: str, password: str):
        from app.database import supabase
        try:
            return supabase.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            raise Exception(f"Login error: {e}")

    @staticmethod
    def sync_user_profile(user_data: UserCreate) -> bool:
        # only create if they don't exist yet
        if not db_user_exists(user_data.id):
            username = user_data.username or user_data.email.split("@")[0]
            return db_create_user(user_data.id, username)
        return True

    @staticmethod
    def upgrade_subscription(user_id: str, subscription: str) -> bool:
        return db_update_user_subscription(user_id, subscription)


auth_service = AuthService()
