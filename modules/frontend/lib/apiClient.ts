/**
 * API Client for communicating with the backend API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3030';

export interface ImageUrl {
  id: string;
  url: string;
  title?: string;
  description?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateImageRequest {
  url: string;
  title?: string;
  description?: string;
  tags?: string[];
}

export interface SearchSimilarRequest {
  image_url: string;
  catalog_name?: string;
}

export interface SimilarProduct {
  brand_name: string | null;
  category: string | null;
  currency: string;
  gender: string;
  id: string;
  images: string[];
  matching_image: string;
  name: string;
  price: string;
  reduced_price: string | null;
  score: number;
  sub_category: string | null;
  url: string;
  vendor: string | null;
}

export interface DetectedItem {
  area: number;
  bouding_box: {
    bottom: number;
    left: number;
    right: number;
    top: number;
  };
  detection_confidence: number;
  item_image: string;
  name: string;
  category: string;
}

export interface ResultGroup {
  average_score: number;
  detected_item: DetectedItem;
  max_score: number;
  rank_score: number;
  similar_products: SimilarProduct[];
}

export interface SearchSimilarResponse {
  data: {
    query_image: string;
    result_groups: ResultGroup[];
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Fetch all image URLs
   */
  async getImages(limit: number = 50, offset: number = 0): Promise<ImageUrl[]> {
    const response = await fetch(
      `${this.baseUrl}/images?limit=${limit}&offset=${offset}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch images: ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Create a new image URL
   */
  async createImage(data: CreateImageRequest): Promise<ImageUrl> {
    const response = await fetch(`${this.baseUrl}/images`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Failed to create image');
    }
    
    return response.json();
  }

  /**
   * Delete an image URL
   */
  async deleteImage(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/images/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete image: ${response.statusText}`);
    }
  }

  /**
   * Search for similar products using Lykdat visual search
   */
  async searchSimilarProducts(data: SearchSimilarRequest): Promise<SearchSimilarResponse> {
    const response = await fetch(`${this.baseUrl}/images/search-similar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Failed to search for similar products');
    }
    
    return response.json();
  }
}

export const apiClient = new ApiClient();
