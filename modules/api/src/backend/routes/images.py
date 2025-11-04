"""
Image URL management routes.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from ..couchbase.collections.images import ImagesDoc, ImagesCollection, ListParams
from ..utils import log

logger = log.get_logger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


class CreateImageRequest(BaseModel):
    """Request model for creating an image."""
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = []


class UpdateImageRequest(BaseModel):
    """Request model for updating an image."""
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


def get_images_collection(request: Request) -> ImagesCollection:
    """Get the images collection from the app state."""
    if not hasattr(request.app.state, 'couchbase_client'):
        raise HTTPException(status_code=503, detail="Couchbase is not configured")
    return ImagesCollection(request.app.state.couchbase_client)


@router.post("", response_model=ImagesDoc, status_code=201)
async def create_image(request: Request, image_request: CreateImageRequest):
    """
    Create a new image URL entry.
    
    This endpoint stores a new image URL along with optional metadata like title,
    description, and tags.
    """
    collection = get_images_collection(request)
    
    # Create the image document
    image_doc = ImagesDoc(
        url=image_request.url,
        title=image_request.title,
        description=image_request.description,
        tags=image_request.tags
    )
    
    # Store in Couchbase
    result = await collection.upsert(image_doc)
    logger.info(f"Created image with ID: {result.id}")
    
    return result


@router.get("/{image_id}", response_model=ImagesDoc)
async def get_image(request: Request, image_id: UUID):
    """
    Retrieve an image URL by ID.
    
    Returns the image document including the URL and all associated metadata.
    """
    collection = get_images_collection(request)
    
    image = await collection.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found")
    
    return image


@router.get("", response_model=list[ImagesDoc])
async def list_images(
    request: Request,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip")
):
    """
    List all image URLs with pagination.
    
    Returns a paginated list of all stored image URLs.
    """
    collection = get_images_collection(request)
    
    params = ListParams(limit=limit, offset=offset)
    images = await collection.list(params)
    
    return images


@router.put("/{image_id}", response_model=ImagesDoc)
async def update_image(request: Request, image_id: UUID, update_request: UpdateImageRequest):
    """
    Update an existing image URL entry.
    
    Allows updating the URL, title, description, or tags of an existing image.
    """
    collection = get_images_collection(request)
    
    # Get existing image
    existing_image = await collection.get(image_id)
    if not existing_image:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found")
    
    # Update fields that were provided
    update_data = update_request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_image, field, value)
    
    # Update timestamp
    from datetime import datetime
    existing_image.updated_at = datetime.utcnow().isoformat()
    
    # Save to Couchbase
    result = await collection.upsert(existing_image)
    logger.info(f"Updated image with ID: {image_id}")
    
    return result


@router.delete("/{image_id}", status_code=204)
async def delete_image(request: Request, image_id: UUID):
    """
    Delete an image URL entry.
    
    Permanently removes an image URL entry from the database.
    """
    collection = get_images_collection(request)
    
    success = await collection.delete(image_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found")
    
    logger.info(f"Deleted image with ID: {image_id}")
    return None
