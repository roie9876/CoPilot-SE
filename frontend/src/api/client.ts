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
      requirements: requirements,
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
 * Submit clarification answers and continue workflow
 */
export async function submitClarification(
  sessionId: string,
  answers: Record<string, string>
): Promise<OrchestratorOutput> {
  try {
    const response = await apiClient.post<OrchestratorOutput>('/api/clarify', {
      session_id: sessionId,
      answers: answers,
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to submit clarification');
    }
    throw error;
  }
}

/**
 * Approve a stage and continue to next stage
 */
export async function approveStage(
  sessionId: string,
  stage: string,
  action: 'approve' | 'modify' | 'back' | 'see_alternatives',
  options?: {
    answers?: Record<string, string>;
    modification_request?: string;
    selected_alternative?: string;
    feedback?: string;
  }
): Promise<OrchestratorOutput> {
  try {
    const response = await apiClient.post<OrchestratorOutput>('/api/stage/approve', {
      session_id: sessionId,
      stage: stage,
      action: action,
      answers: options?.answers || null,
      modification_request: options?.modification_request || null,
      selected_alternative: options?.selected_alternative || null,
      feedback: options?.feedback || null,
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      throw new Error(apiError?.error || error.message || 'Failed to approve stage');
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
