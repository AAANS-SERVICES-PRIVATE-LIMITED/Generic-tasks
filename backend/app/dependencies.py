# api dependencies

from fastapi import Depends, Header, HTTPException, status
from app.services.db import db_get_user, db_get_monthly_message_count
from app.config import SUBSCRIPTION_LIMITS


def get_current_user(x_user_id: str = Header(..., alias="x-user-id")):
    """Fetch the current user from DB using the x-user-id header."""
    user_data = db_get_user(x_user_id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or invalid user ID.",
        )

    return user_data


def check_message_limit(current_user: dict = Depends(get_current_user)):
    """Block the request if the user has exceeded their monthly message limit."""
    user_id = current_user["id"]
    sub_tier = current_user.get("subscription", "free")

    limit = SUBSCRIPTION_LIMITS.get(sub_tier, 10)

    # None means unlimited (pro tier)
    if limit is None:
        return current_user

    count = db_get_monthly_message_count(user_id)
    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Monthly message limit reached ({count}/{limit}). Please upgrade your plan."
        )

    return current_user
