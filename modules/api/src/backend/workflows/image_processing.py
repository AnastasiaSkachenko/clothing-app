"""
Image Processing Workflow

This workflow manages the state of image processing, including:
- Storing image metadata
- Running visual similarity searches
- Handling retries and failures
"""

from datetime import timedelta
from typing import Optional
from dataclasses import dataclass
from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from ..couchbase.collections.images import ImagesDoc
from ..clients.lykdat import LykdatClient
from ..conf import get_lykdat_api_key
from ..utils.log import get_logger

logger = get_logger(__name__)


# Activities

@activity.defn
async def store_image_metadata(url: str, title: Optional[str], description: Optional[str], tags: list[str]) -> str:
    """Store image metadata in Couchbase."""
    logger.info(f"Storing metadata for image: {url}")
    
    # Create the image document with metadata
    image_doc = ImagesDoc(
        url=url,
        title=title,
        description=description,
        tags=tags
    )
    
    logger.info(f"Created image document with ID: {image_doc.id}")
    return str(image_doc.id)


@activity.defn
async def run_similarity_search(image_id: str, image_url: str) -> dict:
    """Run visual similarity search using Lykdat API."""
    logger.info(f"Running similarity search for image {image_id}: {image_url}")
    
    try:
        api_key = get_lykdat_api_key()
        lykdat_client = LykdatClient(api_key)
        
        results = await lykdat_client.search_by_image(image_url=image_url)
        
        num_results = len(results.get('data', {}).get('result_groups', []))
        logger.info(f"Found {num_results} result groups for image {image_id}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in similarity search for image {image_id}: {str(e)}")
        raise


# Workflow

@workflow.defn
class ImageProcessingWorkflow:
    """
    Workflow for processing images with state management.
    
    This workflow:
    1. Stores image metadata
    2. Optionally runs visual similarity search
    3. Tracks processing state throughout
    4. Handles failures with retries
    """
    
    @workflow.run
    async def run(
        self,
        url: str,
        title: str = "",
        description: str = "",
        tags: list[str] = None,
        run_similarity_search: bool = True
    ) -> dict:
        """Execute the image processing workflow."""
        
        if tags is None:
            tags = []
        
        try:
            # Step 1: Store image metadata
            image_id = await workflow.execute_activity(
                store_image_metadata,
                args=[url, title or None, description or None, tags],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                )
            )
            
            # Step 2: Run similarity search if requested
            similarity_completed = False
            if run_similarity_search:
                try:
                    await workflow.execute_activity(
                        run_similarity_search,
                        args=[image_id, url],
                        start_to_close_timeout=timedelta(seconds=60),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=2),
                            maximum_interval=timedelta(seconds=20),
                            backoff_coefficient=2.0,
                        )
                    )
                    
                    similarity_completed = True
                except Exception as e:
                    logger.error(f"Similarity search failed: {str(e)}")
                    # Continue even if similarity search fails
            
            return {
                "image_id": image_id,
                "url": url,
                "similarity_search_completed": similarity_completed,
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Image processing workflow failed: {str(e)}")
            
            return {
                "url": url,
                "similarity_search_completed": False,
                "error": str(e),
                "status": "failed"
            }
