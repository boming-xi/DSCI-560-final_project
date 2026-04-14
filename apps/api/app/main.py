from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_settings, get_vector_store
from app.api.v1.router import router as api_v1_router
from app.core.logging import configure_logging
from app.db.bootstrap import bootstrap_reference_data

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_reference_data(settings)
    yield
    get_vector_store().close()


app = FastAPI(
    title="AI Healthcare Assistant API",
    version="0.1.0",
    description="Demo backend for symptom triage, insurance matching, doctor ranking, and booking.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Healthcare Assistant API is running."}
