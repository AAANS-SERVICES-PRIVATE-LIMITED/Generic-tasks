from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.auth import auth_service
from app.schemas.user import UserCreate, AuthRequest
from app.dependencies import get_current_user
from app.services.db import db_get_monthly_message_count
from app.config import SUBSCRIPTION_LIMITS

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup(request: AuthRequest):
    # register new user
    try:
        response = auth_service.signup(request.email, request.password)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(request: AuthRequest):
    # log in user
    try:
        response = auth_service.login(request.email, request.password)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_profile(user_data: UserCreate):
    # copy supabase user to local db
    success = auth_service.sync_user_profile(user_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync user profile")
    return {"status": "success"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # get current user info and append monthly message usage
    user_id = current_user["id"]
    sub_tier = current_user.get("subscription", "free")
    
    current_user["message_count"] = db_get_monthly_message_count(user_id)
    current_user["message_limit"] = SUBSCRIPTION_LIMITS.get(sub_tier, 10)
    
    return current_user


class UpgradeRequest(BaseModel):
    subscription: str


@router.post("/upgrade")
async def upgrade_subscription(
    request: UpgradeRequest,
    current_user: dict = Depends(get_current_user),
):
    # upgrade user subscription tier
    success = auth_service.upgrade_subscription(current_user["id"], request.subscription)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")
    return {"status": "success", "subscription": request.subscription}
