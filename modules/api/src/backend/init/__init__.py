"""Centralized initialization and deinitialization for the API."""

from fastapi import FastAPI

from .temporal import init_temporal, deinit_temporal

from .couchbase import init_couchbase, deinit_couchbase


async def init(app: FastAPI) -> None:
    """Initialize all components during app startup."""
    await init_temporal(app)
    await init_couchbase(app)
    pass


async def deinit(app: FastAPI) -> None:
    """Deinitialize all components during app shutdown."""
    await deinit_temporal(app)
    await deinit_couchbase(app)
    pass
