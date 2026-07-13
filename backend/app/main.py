from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.web.auth import router as web_auth_router
from app.api.admin.auth import router as admin_auth_router
from app.core.config import settings
from app.models.user import Base
from app.db.session import engine

app = FastAPI(title="EC Main API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ec-backend"}


app.include_router(web_auth_router, prefix="/api/v1/web")
app.include_router(admin_auth_router, prefix="/api/v1/admin")
