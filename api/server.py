"""
FastAPI Server for Co-Pilot SE Web Portal
Provides REST API endpoints for the frontend React application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.models.schemas import OrchestratorOutput

# Initialize FastAPI app
app = FastAPI(
    title="Co-Pilot SE API",
    description="Multi-cloud architecture generation API",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator (singleton)
orchestrator = None


def get_orchestrator() -> MasterOrchestrator:
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = MasterOrchestrator()
    return orchestrator


# Request/Response Models
class GenerateRequest(BaseModel):
    """Request model for architecture generation"""

    requirements: str = Field(
        ...,
        min_length=10,
        description="User requirements for architecture generation",
        json_schema_extra={
            "example": "Design an Azure e-commerce platform for 50,000 users with PCI DSS compliance"
        },
    )


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str


# API Endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns:
        HealthResponse: API health status and version
    """
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/generate", response_model=OrchestratorOutput, tags=["Architecture"])
async def generate_architecture(request: GenerateRequest):
    """
    Generate multi-cloud architecture from requirements

    This endpoint orchestrates all 4 agents sequentially:
    1. Requirements Agent: Parse and extract requirements
    2. Architecture Agent: Design cloud architecture
    3. Cost Agent: Estimate costs
    4. Documentation Agent: Generate HLD document

    Args:
        request: GenerateRequest with user requirements

    Returns:
        OrchestratorOutput: Complete architecture with costs and documentation

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Get orchestrator instance
        orch = get_orchestrator()

        # Run orchestration workflow
        result = await orch.orchestrate(request.requirements)

        # Check for errors
        if result.status == "error":
            raise HTTPException(
                status_code=500,
                detail=result.error_message
                or "Architecture generation failed with unknown error",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information

    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "Co-Pilot SE API",
        "version": "1.0.0",
        "description": "Multi-cloud architecture generation API",
        "endpoints": {
            "health": "/health",
            "generate": "/api/generate (POST)",
            "docs": "/docs",
        },
    }


def main():
    """Run the API server"""
    print("=" * 60)
    print("🚀 Co-Pilot SE API Server")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Frontend CORS: localhost:5173, localhost:3000")
    print("=" * 60)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
