import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.payments import router as payments_router
from app.api.v1.plans import router as plans_router
from app.api.v1.settings import router as settings_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.core.database import engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup & shutdown logic."""
    # Ensure database schema is created on startup (especially for async SQLite / local development)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Subscription Management System API",
        description="Multi-tenant B2B subscription operations platform API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    origins = [
        frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    origins = list(dict.fromkeys(origins))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")
    app.include_router(customers_router, prefix="/api/v1")
    app.include_router(plans_router, prefix="/api/v1")
    app.include_router(subscriptions_router, prefix="/api/v1")
    app.include_router(invoices_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, Any]:
        return {
            "name": "Subscription Management System API",
            "version": "1.0.0",
            "status": "online",
            "documentation": "/docs",
        }

    @app.get("/health", tags=["Monitoring"], status_code=status.HTTP_200_OK)
    @app.get("/api/v1/health", tags=["Monitoring"], status_code=status.HTTP_200_OK)
    async def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "app": "subscription-management-system",
            "version": "1.0.0",
            "environment": os.getenv("APP_ENV", "development"),
        }

    return app


app = create_app()
