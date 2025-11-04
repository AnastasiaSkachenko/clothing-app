"""Couchbase client initialization and deinitialization."""

from fastapi import FastAPI

from couchbase_client import CouchbaseClient
from ..conf.couchbase import get_couchbase_conf
from ..couchbase.collections import COLLECTIONS
from ..utils.log import get_logger

logger = get_logger(__name__)


async def init_couchbase(app: FastAPI) -> None:
    """Initialize Couchbase client and collections."""
    logger.info("Initializing Couchbase client...")
    couchbase_config = get_couchbase_conf()
    app.state.couchbase_client = CouchbaseClient(couchbase_config)
    await app.state.couchbase_client.init_connection()
    logger.info("Couchbase client connected successfully")

    if not COLLECTIONS:
        logger.info("No Couchbase collections found. You can add collections using the add-couchbase-collection tool.")
    else:
        logger.info(f"Initializing {len(COLLECTIONS)} Couchbase collection(s)...")
        for Collection in COLLECTIONS:
            await Collection(app.state.couchbase_client).initialize()
        logger.info(f"All {len(COLLECTIONS)} Couchbase collection(s) initialized successfully")


async def deinit_couchbase(app: FastAPI) -> None:
    """Close Couchbase client connection."""
    logger.info("Closing Couchbase client connection...")
    await app.state.couchbase_client.close()
    logger.info("Couchbase client connection closed")
