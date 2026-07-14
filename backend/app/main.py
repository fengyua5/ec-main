import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
from fastapi.middleware.cors import CORSMiddleware
from app.api.web.ai import router as web_ai_router
from app.api.web.auth import router as web_auth_router
from app.api.admin.auth import router as admin_auth_router
from app.api.admin.ai_faq import router as admin_ai_faq_router
from app.api.admin.ai_chat import router as admin_ai_chat_router
from app.core.config import settings
from app.models.user import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="EC Main API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ec-backend"}


app.include_router(web_ai_router, prefix="/api/v1/web")
app.include_router(web_auth_router, prefix="/api/v1/web")
app.include_router(admin_auth_router, prefix="/api/v1/admin")
app.include_router(admin_ai_faq_router, prefix="/api/v1/admin")
app.include_router(admin_ai_chat_router, prefix="/api/v1/admin")
