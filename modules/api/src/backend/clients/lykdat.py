"""Lykdat API client for visual search."""

import httpx
from typing import Any

from ..utils.log import get_logger

logger = get_logger(__name__)


class LykdatClient:
    """Client for interacting with Lykdat visual search API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloudapi.lykdat.com/v1"
    
    async def search_by_image(
        self, 
        image_url: str, 
        catalog_name: str = None
    ) -> dict[str, Any]:
        """
        Search for similar products based on an image URL.
        
        Args:
            image_url: URL of the image to search for
            catalog_name: Name of the catalog to search in (optional, uses global search if not provided)
            
        Returns:
            Dictionary containing search results with similar products
        """
        url = f"{self.base_url}/global/search"
        
        payload = {
            "api_key": self.api_key,
            "image_url": image_url
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Lykdat API request failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Lykdat API request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Lykdat API: {str(e)}")
            raise
