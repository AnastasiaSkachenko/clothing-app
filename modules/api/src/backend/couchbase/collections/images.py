"""
Bindings for working with the 'images' collection.
"""

from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from couchbase_client import CouchbaseClient


# The type used for keys in this collection.
_KEY_TYPE = UUID

# The collection name in Couchbase
_COLLECTION_NAME = "images"


class ImagesDoc(BaseModel):
    """Model for images rows."""
    id: _KEY_TYPE = Field(default_factory=uuid4)
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ListParams(BaseModel):
    """Supported parameters for images list operations."""
    # Add more params here as needed
    limit: int = 50
    offset: int = 0


class ImagesCollection:
    """Bindings for working with the 'images' Couchbase collection"""

    def __init__(self, client: CouchbaseClient):
        self._client = client
        self._collection = None

    ## Utils ##

    async def _get_collection(self):
        """Get the collection handle, creating it if necessary."""
        if not self._collection:
            keyspace = self._client.get_keyspace(_COLLECTION_NAME)
            self._collection = await self._client.get_collection(keyspace)
        return self._collection

    ## Initialization ##

    async def initialize(self):
        """Creates the collection if it doesn't already exist, and stores a handle to it."""
        await self._get_collection()

    ## Operations ##

    async def _get_doc(self, id: _KEY_TYPE) -> dict | None:
        """Retrieves a images doc as a plain dict."""
        await self._get_collection()
        keyspace = self._client.get_keyspace(_COLLECTION_NAME)
        return await self._client.get_document(keyspace, str(id))

    async def get(self, id: _KEY_TYPE) -> ImagesDoc | None:
        """Retrieves a images doc as a ImagesDoc."""
        doc = await self._get_doc(id)
        if doc is None:
            return None
        doc['id'] = id
        return ImagesDoc(**doc)

    async def _list_rows(self, params: ListParams | None = None) -> list[dict]:
        """Retrieves images docs as a list of plain dicts."""
        params = params or ListParams()
        keyspace = self._client.get_keyspace(_COLLECTION_NAME)
        query = self._client.build_list_query(keyspace, limit=params.limit, offset=params.offset)
        return await self._client.query_documents(query)

    async def list(self, params: ListParams | None = None) -> list[ImagesDoc]:
        """Retrieves a list of images docs as ImagesDoc instances."""
        rows = await self._list_rows(params)
        return [ImagesDoc(**{**row, 'id': row.get('id')}) for row in rows]

    async def delete(self, id: _KEY_TYPE) -> bool:
        """Delete a images doc."""
        keyspace = self._client.get_keyspace(_COLLECTION_NAME)
        return await self._client.delete_document(keyspace, str(id))

    async def upsert(self, doc: ImagesDoc) -> ImagesDoc:
        """Insert or update a images doc."""
        keyspace = self._client.get_keyspace(_COLLECTION_NAME)
        await self._client.upsert_document(keyspace, str(doc.id), doc.model_dump(mode='json'))
        return doc
