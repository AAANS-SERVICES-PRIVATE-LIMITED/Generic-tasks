from fastapi import FastAPI
from routers import send_router, templates_router
import uvicorn

app = FastAPI(title="Email API", version="1.0.0")

# Include routers
app.include_router(send_router, prefix="/api")
app.include_router(templates_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
