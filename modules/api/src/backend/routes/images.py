"""
Image URL management routes.
"""

from typing import Optional, Any
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from ..couchbase.collections.images import ImagesDoc, ImagesCollection, ListParams
from ..clients.lykdat import LykdatClient
from ..conf import get_lykdat_api_key
from ..workflows.image_processing import ImageProcessingWorkflow
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


class SearchSimilarRequest(BaseModel):
    """Request model for searching similar products."""
    image_url: HttpUrl


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


@router.post("/search-similar", response_model=dict[str, Any])
async def search_similar_products(request: Request, search_request: SearchSimilarRequest):
    """
    Search for similar products based on an image URL using Lykdat visual search API.
    
    This endpoint takes an image URL and returns visually similar products from the catalog.
    """
    try:
        # Initialize Lykdat client
        api_key = get_lykdat_api_key()
        lykdat_client = LykdatClient(api_key)
        
        # Perform the search
        logger.info(f"Searching for similar products for image: {search_request.image_url}")
        results = await lykdat_client.search_by_image(
            image_url=str(search_request.image_url)
        )
        
        logger.info(f"Found {len(results.get('data', {}).get('result_groups', []))} result groups")
        return results
        
    except Exception as e:
        logger.error(f"Error searching for similar products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search for similar products: {str(e)}"
        )


@router.post("/process", response_model=dict[str, Any], status_code=202)
async def process_image_with_workflow(request: Request, image_request: CreateImageRequest):
    """
    Process an image using Temporal workflow for state management.
    
    This endpoint:
    1. Starts a Temporal workflow to manage the image processing state
    2. Stores image metadata in Couchbase
    3. Optionally runs visual similarity search
    4. Returns workflow ID for tracking progress
    
    The workflow handles retries, failure recovery, and maintains processing state.
    """
    if not hasattr(request.app.state, 'temporal_client'):
        raise HTTPException(status_code=503, detail="Temporal is not configured")
    
    try:
        temporal_client = request.app.state.temporal_client
        
        # Generate a unique workflow ID
        workflow_id = f"image-processing-{UUID.uuid4()}"
        
        # Start the workflow with simplified parameters
        logger.info(f"Starting image processing workflow: {workflow_id}")
        handle = await temporal_client.client.start_workflow(
            ImageProcessingWorkflow.run,
            args=[
                str(image_request.url),
                image_request.title,
                image_request.description,
                image_request.tags,
                True  # run_similarity_search
            ],
            id=workflow_id,
            task_queue=temporal_client.config.task_queue,
        )
        
        logger.info(f"Workflow started with ID: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "status": "processing",
            "message": "Image processing workflow started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting image processing workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start image processing workflow: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/status", response_model=dict[str, Any])
async def get_workflow_status(request: Request, workflow_id: str):
    """
    Get the current status of an image processing workflow.
    
    Returns the workflow state including processing status, completion status,
    and any results or errors.
    """
    if not hasattr(request.app.state, 'temporal_client'):
        raise HTTPException(status_code=503, detail="Temporal is not configured")
    
    try:
        temporal_client = request.app.state.temporal_client
        
        # Get the workflow handle
        handle = temporal_client.client.get_workflow_handle(workflow_id)
        
        # Query the workflow state
        state = await handle.query(ImageProcessingWorkflow.get_state)
        
        return {
            "workflow_id": workflow_id,
            "state": state.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/result", response_model=dict[str, Any])
async def get_workflow_result(request: Request, workflow_id: str):
    """
    Get the final result of a completed image processing workflow.
    
    This endpoint waits for the workflow to complete and returns the result.
    If the workflow is still running, it will wait until completion.
    """
    if not hasattr(request.app.state, 'temporal_client'):
        raise HTTPException(status_code=503, detail="Temporal is not configured")
    
    try:
        temporal_client = request.app.state.temporal_client
        
        # Get the workflow handle
        handle = temporal_client.client.get_workflow_handle(workflow_id)
        
        # Wait for the workflow to complete and get result
        logger.info(f"Waiting for workflow {workflow_id} to complete...")
        result = await handle.result()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow result: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow result: {str(e)}"
        )
