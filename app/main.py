"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, engine, SessionLocal
from app.api.v1.router import api_router
import app.models  # noqa: F401  -- ensures all models are registered

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
logger = logging.getLogger(__name__)


def create_tables():
    Base.metadata.create_all(bind=engine)


def bootstrap_admin():
    from app.models import AdminUser, AdminRole
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
        if existing:
            return
        a = AdminUser(
            email=settings.ADMIN_EMAIL,
            full_name="Super Admin",
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=AdminRole.SUPERADMIN,
            is_active=True,
        )
        db.add(a)
        db.commit()
        logger.info(f"✅ Bootstrap admin created: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    create_tables()
    bootstrap_admin()
    logger.info(f"🚀 {settings.APP_NAME} started in {settings.APP_ENV} mode")
    yield
    logger.info("👋 Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Self-drive vehicle rental backend.\n\n"
        "**Roles**: User (rider), Partner (vehicle provider), Admin (operations).\n\n"
        "Auth uses phone-OTP for users/partners, email/password for admins.\n"
        "All protected endpoints require `Authorization: Bearer <access_token>`."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violated", "error": str(exc.orig)},
    )


# Static uploads (DEV ONLY — use S3/CloudFront for prod)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base": settings.API_V1_PREFIX,
    }
