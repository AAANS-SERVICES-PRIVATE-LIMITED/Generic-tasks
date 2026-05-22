from app.schemas.chat import ChatCreate
from app.schemas.message import MessageCreate
from app.services.db import (
    db_create_chat,
    db_get_user_chats,
    db_get_chat_messages,
    db_save_message,
    db_delete_chat,
)


class ChatService:
    @staticmethod
    def create_chat(chat_data: ChatCreate):
        return db_create_chat(chat_data.user_id, chat_data.title)

    @staticmethod
    def save_message(message_data: MessageCreate, image_url: str = None):
        return db_save_message(message_data.chat_id, message_data.role, message_data.content, image_url)

    @staticmethod
    def get_chat_history(chat_id: str):
        return db_get_chat_messages(chat_id)

    @staticmethod
    def get_user_chats(user_id: str):
        return db_get_user_chats(user_id)

    @staticmethod
    def delete_chat(chat_id: str):
        return db_delete_chat(chat_id)

    @staticmethod
    def handle_chat_message(user_id: str, message_content: str, chat_id: str = None, base64_image: str = None):
        """Orchestration: handles chat creation + saving user message in one call."""
        final_chat_id = chat_id
        if not final_chat_id:
            new_chat = db_create_chat(user_id, message_content[:40])
            final_chat_id = new_chat["id"]

        db_save_message(final_chat_id, "user", message_content, image_url=base64_image)
        return final_chat_id


chat_service = ChatService()
