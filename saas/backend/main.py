"""
卧龙 SaaS — FastAPI 入口
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import get_settings
from .database import create_tables
from .auth.router import router as auth_router
from .whatsapp.router import router as wa_router

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="卧龙 SaaS API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.frontend_url, "http://localhost:5173", "http://localhost:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(wa_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Serve React frontend (SPA fallback)
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str):
            index = FRONTEND_DIST / "index.html"
            return FileResponse(str(index))

    return app


app = create_app()
