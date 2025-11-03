import axios from 'axios';
import type {
  KGStartRequest,
  KGStartResponse,
  KGAnswerRequest,
  KGAnswerResponse,
  KGStatusResponse,
  KGArchitectureRequest,
  KGArchitectureResponse,
} from '../types-kg';
import type { ApiError } from '../types';

// API base URL - will use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Start Knowledge Graph requirements gathering session
 */
export async function kgStart(requirements: string): Promise<KGStartResponse> {
  try {
    const request: KGStartRequest = { requirements };
    const response = await apiClient.post<KGStartResponse>('/api/kg/start', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to start KG session');
    }
    throw error;
  }
}

/**
 * Submit answers for a specific domain
 */
export async function kgAnswer(
  sessionId: string,
  domain: string,
  answers: Record<string, string | number | boolean | string[]>
): Promise<KGAnswerResponse> {
  try {
    const request: KGAnswerRequest = {
      session_id: sessionId,
      domain,
      answers,
    };
    const response = await apiClient.post<KGAnswerResponse>('/api/kg/answer', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to submit answers');
    }
    throw error;
  }
}

/**
 * Get current Knowledge Graph status
 */
export async function kgStatus(sessionId: string): Promise<KGStatusResponse> {
  try {
    const response = await apiClient.get<KGStatusResponse>(`/api/kg/status/${sessionId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to get KG status');
    }
    throw error;
  }
}

/**
 * Generate architecture from completed Knowledge Graph
 */
export async function kgArchitecture(sessionId: string): Promise<KGArchitectureResponse> {
  try {
    const request: KGArchitectureRequest = { session_id: sessionId };
    const response = await apiClient.post<KGArchitectureResponse>(
      '/api/kg/architecture',
      request
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(
        apiError?.error || error.message || 'Failed to generate architecture from KG'
      );
    }
    throw error;
  }
}
