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
}

export const apiClient = new ApiClient();
