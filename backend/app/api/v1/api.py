# backend/app/api/v1/api.py
from fastapi import APIRouter
from .endpoints import auth, documents, workers, companies, observations

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    workers.router,
    prefix="/workers",
    tags=["workers"]
)

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["companies"]
)

api_router.include_router(
    observations.router,
    prefix="/observations",
    tags=["observations"]
)
