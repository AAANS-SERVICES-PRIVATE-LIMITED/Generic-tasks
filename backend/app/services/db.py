from datetime import datetime
from app.database import supabase


# ─── User Queries ────────────────────────────────────────────────────────────

def db_get_user(user_id: str) -> dict | None:
    """Fetch a user's profile by ID. Falls back gracefully if subscription column is missing."""
    try:
        res = (
            supabase
            .table("table_user")
            .select("id, username, avatar_url, subscription")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        # fallback if subscription column doesn't exist yet
        try:
            res = (
                supabase
                .table("table_user")
                .select("id, username, avatar_url")
                .eq("id", user_id)
                .single()
                .execute()
            )
            user_data = res.data
            if user_data:
                user_data["subscription"] = "free"
            return user_data
        except Exception as e:
            print(f"DB Error (db_get_user): {e}")
            return None


def db_user_exists(user_id: str) -> bool:
    """Check if a user row exists in the table."""
    try:
        res = supabase.table("table_user").select("id").eq("id", user_id).execute()
        return bool(res.data)
    except Exception as e:
        print(f"DB Error (db_user_exists): {e}")
        return False


def db_create_user(user_id: str, username: str) -> bool:
    """Insert a new user row."""
    try:
        supabase.table("table_user").insert({
            "id": user_id,
            "username": username,
            "avatar_url": None
        }).execute()
        return True
    except Exception as e:
        print(f"DB Error (db_create_user): {e}")
        return False


def db_update_user_subscription(user_id: str, subscription: str) -> bool:
    """Update a user's subscription tier."""
    try:
        supabase.table("table_user").update({"subscription": subscription}).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"DB Error (db_update_user_subscription): {e}")
        return False


# ─── Message Queries ─────────────────────────────────────────────────────────

def db_get_monthly_message_count(user_id: str) -> int:
    """Count all messages sent by a user in the current calendar month."""
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # get all chat ids belonging to the user
    res_chats = supabase.table("table_chats").select("id").eq("user_id", user_id).execute()
    if not res_chats.data:
        return 0

    chat_ids = [chat["id"] for chat in res_chats.data]

    # count user messages in those chats this month
    res_messages = (
        supabase.table("table_messages")
        .select("id", count="exact")
        .in_("chat_id", chat_ids)
        .eq("role", "user")
        .gte("created_at", start_of_month)
        .execute()
    )
    return res_messages.count if res_messages.count is not None else 0


def db_get_chat_messages(chat_id: str) -> list:
    """Fetch all messages for a chat, ordered by time."""
    try:
        res = (
            supabase.table("table_messages")
            .select("*")
            .eq("chat_id", chat_id)
            .order("created_at")
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"DB Error (db_get_chat_messages): {e}")
        return []


def db_save_message(chat_id: str, role: str, content: str, image_url: str = None) -> dict | None:
    """Insert a single message row, generating its embedding on the fly."""
    try:
        from app.services.embeddings import embedding_service
        
        # Generate the math vector for this message's content
        vector = embedding_service.generate_embedding(content)
        
        data = {
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "embedding": vector
        }
        if image_url:
            data["image_url"] = image_url

        res = supabase.table("table_messages").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"DB Error (db_save_message): {e}")
        return None


# ─── Chat Queries ─────────────────────────────────────────────────────────────

def db_create_chat(user_id: str, title: str) -> dict | None:
    """Insert a new chat row and return it."""
    try:
        res = supabase.table("table_chats").insert({
            "user_id": user_id,
            "title": title or "New Chat"
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"DB Error (db_create_chat): {e}")
        return None


def db_get_user_chats(user_id: str) -> list:
    """Fetch all chats for a user, newest first."""
    try:
        res = (
            supabase.table("table_chats")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"DB Error (db_get_user_chats): {e}")
        return []


def db_delete_chat(chat_id: str) -> bool:
    """Delete a chat and all its messages."""
    try:
        supabase.table("table_messages").delete().eq("chat_id", chat_id).execute()
        supabase.table("table_chats").delete().eq("id", chat_id).execute()
        return True
    except Exception as e:
        return False

# ─── Documents (PDF RAG) ──────────────────────────────────────────────────────

def db_save_document_chunks(chat_id: str, chunks_data: list) -> bool:
    """Insert multiple document chunks into table_document_chunks."""
    try:
        # chunks_data should be a list of dicts: {"chat_id": ..., "content": ..., "embedding": ...}
        if not chunks_data:
            return True
        supabase.table("table_document_chunks").insert(chunks_data).execute()
        return True
    except Exception as e:
        print(f"DB Error (db_save_document_chunks): {e}")
        return False

def db_search_document_chunks(chat_id: str, query_embedding: list, match_threshold: float = 0.3, match_count: int = 4) -> list:
    """Search for relevant chunks using the match_document_chunks RPC."""
    try:
        res = supabase.rpc("match_document_chunks", {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
            "target_chat_id": chat_id
        }).execute()
        return res.data
    except Exception as e:
        print(f"DB Error (db_search_document_chunks): {e}")
        return []


def db_get_document_chunks_sample(chat_id: str, limit: int = 6) -> list:
    """Fallback: fetch the first N chunks for a chat when semantic search finds nothing."""
    try:
        res = (
            supabase.table("table_document_chunks")
            .select("content")
            .eq("chat_id", chat_id)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"DB Error (db_get_document_chunks_sample): {e}")
        return []
