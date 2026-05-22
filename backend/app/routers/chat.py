from fastapi import APIRouter, Depends, HTTPException
from app.schemas.chat import ChatCreate
from app.schemas.message import MessageCreate
from app.services.chat import chat_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


# chat endpoints

@router.post("/new")
async def create_new_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_user),
):
    # start a new chat thread
    chat = chat_service.create_chat(chat_data)
    if not chat:
        raise HTTPException(status_code=500, detail="Failed to create chat")
    return chat


@router.post("/message")
async def save_chat_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
):
    # save a chat message
    message = chat_service.save_message(message_data)
    if not message:
        raise HTTPException(status_code=500, detail="Failed to save message")
    return message


@router.get("/history/{chat_id}")
async def get_history(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    # get messages for a chat
    return chat_service.get_chat_history(chat_id)


@router.get("/list/{user_id}")
async def get_user_chats(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    # list all chats for a user
    return chat_service.get_user_chats(user_id)


@router.delete("/delete/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    # delete a chat thread
    success = chat_service.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete chat")
    return {"status": "success"}
