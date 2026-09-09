"""FastAPI application factory.

Run locally:

    uv run uvicorn backend.main:app --reload --port 8000

or

    uv run python -m backend.main

The API is mounted under ``/api``; a plain ``/health`` is also exposed at
the root for load balancers. CORS allows the Vite dev server
(``http://localhost:5173``) — there is no authentication yet.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agency_routes import agency_router
from .causal_routes import causal_router
from .collision_routes import collision_router
from .counterfactual_routes import router as counterfactual_router
from .detective_routes import detective_router
from .forensics_routes import forensics_router
from .genome_routes import genome_router
from .lab_routes import router as lab_router
from .memory_routes import router as memory_router
from .routes import router
from .observatory_routes import observatory_router
from .fingerprint_routes import fingerprint_router
from .ecosystem_routes import ecosystem_router
from .studio_routes import studio_router
from .research_routes import research_router
from .store import ExperimentStore
from .surgery_routes import surgery_router
from .synaptic_routes import synaptic_router
from .xray_routes import xray_router

DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


def create_app(store: ExperimentStore | None = None) -> FastAPI:
    app = FastAPI(
        title="Neural Archaeology",
        description=(
            "Educational AI research platform — excavate the hidden life of "
            "machine memory. Deterministic, explainable state-update "
            "mechanisms on a fixed-dimensional substrate."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.store = store or ExperimentStore()
    app.include_router(router, prefix="/api")
    app.include_router(memory_router, prefix="/api")
    app.include_router(lab_router, prefix="/api")
    app.include_router(counterfactual_router, prefix="/api")
    app.include_router(agency_router, prefix="/api")
    app.include_router(xray_router, prefix="/api")
    app.include_router(detective_router, prefix="/api")
    app.include_router(genome_router, prefix="/api")
    app.include_router(causal_router, prefix="/api")
    app.include_router(synaptic_router, prefix="/api")
    app.include_router(surgery_router, prefix="/api")
    app.include_router(collision_router, prefix="/api")
    app.include_router(forensics_router, prefix="/api")
    app.include_router(observatory_router, prefix="/api")
    app.include_router(fingerprint_router, prefix="/api")
    app.include_router(ecosystem_router, prefix="/api")
    app.include_router(studio_router)
    app.include_router(research_router)

    @app.get("/health")
    def root_health() -> dict:
        from core.experiment import SCHEMA_VERSION

        return {
            "status": "ok",
            "core_version": __import__("core").__version__,
            "schema_version": SCHEMA_VERSION,
            "api_prefix": "/api",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)