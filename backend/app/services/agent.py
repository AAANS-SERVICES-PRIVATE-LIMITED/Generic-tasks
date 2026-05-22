from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, trim_messages
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage
from app.config import GROQ_API_KEY


# ─── Supported models by provider ─────────────────────────────────────────────

OLLAMA_MODELS = {'llama3.1', 'phi3', 'gemma2:2b'}


# ─── State shape that flows through our LangGraph ─────────────────────────────

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]  # full conversation history
    model_name: str                  # which model the user selected
    chat_id: str                     # used for searching documents


# ─── Node: format + trim context ──────────────────────────────────────────────

def trim_context(state: AgentState) -> AgentState:
    
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4096,          # safe limit for all our models
        strategy="last",          # keep the most recent messages
        token_counter=len,        # simple word-count fallback (works without tiktoken)
        include_system=True,      # always keep the system prompt
    )
    return {**state, "messages": trimmed}


# ─── Node: Retrieve PDF Context (RAG) ─────────────────────────────────────────

def retrieve_context(state: AgentState) -> AgentState:
    from app.services.db import db_search_document_chunks, db_get_document_chunks_sample
    from app.services.embeddings import embedding_service
    
    chat_id = state.get("chat_id")
    if not chat_id:
        return state

    # Extract the user's latest query
    latest_msg = state["messages"][-1]
    if not isinstance(latest_msg, HumanMessage):
        return state

    query = latest_msg.content
    if isinstance(query, list):
        # Extract text if it's a multipart message (image attached)
        query = next((item["text"] for item in query if item.get("type") == "text"), "")

    if not query:
        return state

    # 1. Try semantic search first (threshold lowered to 0.3 for broader matches)
    query_vector = embedding_service.generate_embedding(query)
    matching_chunks = db_search_document_chunks(chat_id, query_vector)

    # 2. Fallback: if semantic search finds nothing, grab the first N chunks directly
    #    This handles vague queries like "tell about this" or "summarize"
    if not matching_chunks:
        matching_chunks = db_get_document_chunks_sample(chat_id, limit=6)

    if matching_chunks:
        context_str = "\n\n".join([f"Snippet:\n{c['content']}" for c in matching_chunks])
        
        messages = list(state["messages"])
        sys_msg = messages[0]
        if isinstance(sys_msg, SystemMessage):
            doc_notice = (
                "\n\nIMPORTANT: The user has uploaded a document to this chat. "
                "Use the document context below to answer their questions. "
                "If they ask vague questions like 'tell about this' or 'summarize', "
                "summarize and explain the document content.\n\n"
                f"--- DOCUMENT CONTEXT ---\n{context_str}\n------------------------"
            )
            messages[0] = SystemMessage(content=sys_msg.content + doc_notice)
        
        return {**state, "messages": messages}

    return state


# ─── Node: pick model + stream response ───────────────────────────────────────

def call_model(state: AgentState):
    
    model_name = state["model_name"]

    if model_name in OLLAMA_MODELS:
        llm = ChatOllama(model=model_name)
    else:
        llm = ChatGroq(model=model_name, api_key=GROQ_API_KEY)

    # Invoke the model. LangGraph's stream_mode="messages" will intercept the stream automatically!
    response = llm.invoke(state["messages"])
    
    # Return the state update dictionary
    return {"messages": [response]}


# ─── Build the LangGraph workflow ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("trim_context", trim_context)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("call_model", call_model)
    
    graph.add_edge(START, "trim_context")
    graph.add_edge("trim_context", "retrieve_context")
    graph.add_edge("retrieve_context", "call_model")
    graph.add_edge("call_model", END)
    return graph.compile()


# ─── Public helper ────────────────────────────────────────────────────────────

def build_messages(system_prompt: str, history: list, base64_image: str = None) -> list:
    
    lc_messages = [SystemMessage(content=system_prompt)]

    for idx, msg in enumerate(history):
        role = msg["role"]
        content = msg["content"] or ""

        # Attach image to the last user message if provided
        is_last = idx == len(history) - 1
        if is_last and role == "user" and base64_image:
            lc_messages.append(HumanMessage(content=[
                {"type": "text", "text": content},
                {"type": "image_url", "image_url": {"url": base64_image}},
            ]))
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))
        else:
            lc_messages.append(AIMessage(content=content))

    return lc_messages


agent_graph = build_graph()
