from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import ALLOWED_ORIGINS
from app.routers.chat import router as chat_router
from app.routers.auth import router as auth_router
from app.routers.ai import router as ai_router
from app.routers.documents import router as documents_router

app = FastAPI(title="S-Chat API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(documents_router, prefix="/api/documents")

@app.get("/")
async def root():
    return {"message": "S-Chat API is running"}