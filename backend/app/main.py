"""FastAPI main application."""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import cases, websocket, utilities, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NEXUS CREDIT Engine...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"DB init skipped (may need PostgreSQL): {e}")

    # Train ML models if needed
    from app.ml.scorer import CreditScorer
    scorer = CreditScorer()
    scorer.ensure_models()
    logger.info("ML models ready")

    # Seed DuckDB demo data
    try:
        from app.db.seed import seed_duckdb
        seed_duckdb()
        logger.info("DuckDB demo data seeded")
    except Exception as e:
        logger.warning(f"DuckDB seed skipped: {e}")

    yield
    logger.info("Shutting down NEXUS CREDIT Engine")


app = FastAPI(
    title="NEXUS CREDIT — AI Credit Decisioning Engine",
    description="Autonomous credit analysis and CAM generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.cors_origins_list else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(websocket.router)
app.include_router(utilities.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "nexus-credit", "version": "1.0.0"}


# Serve frontend static files in production
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = _static_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))
