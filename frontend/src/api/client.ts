import axios from 'axios';
import type { OrchestratorOutput, ApiError } from '../types';

// API base URL - will use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes timeout for architecture generation
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Generate cloud architecture from natural language requirements
 */
export async function generateArchitecture(requirements: string): Promise<OrchestratorOutput> {
  try {
    const response = await apiClient.post<OrchestratorOutput>('/api/generate', {
      user_input: requirements,
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to generate architecture');
    }
    throw error;
  }
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<{ status: string }> {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API server is not reachable');
  }
}
