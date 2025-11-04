"""
FastAPI Server for Co-Pilot SE Web Portal
Provides REST API endpoints for the frontend React application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
import uvicorn
import sys
import logging
import traceback
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Session storage (in-memory for POC - use Redis/DB in production)
sessions: dict = {}


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


class ClarificationRequest(BaseModel):
    """Request model for submitting clarification answers"""

    session_id: str = Field(
        ...,
        description="Session ID from previous NEEDS_CLARIFICATION response",
        json_schema_extra={"example": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
    )

    answers: dict[str, str] = Field(
        ...,
        description="Map of question to answer",
        json_schema_extra={
            "example": {
                "For 99.999% availability, what is your target RTO?": "< 5 minutes",
                "Do you require multi-region deployment?": "Yes, active-active",
            }
        },
    )


class StageApprovalRequest(BaseModel):
    """Request model for stage approval (new multi-stage flow)"""

    session_id: str = Field(..., description="Session ID from previous stage")
    stage: str = Field(..., description="Current stage name")
    action: str = Field(
        ...,
        description="User action: 'approve', 'modify', 'back', or 'see_alternatives'",
        json_schema_extra={"example": "approve"}
    )
    modification_request: str | None = Field(None, description="Optional modification request if action is 'modify'")
    selected_alternative: str | None = Field(None, description="Selected alternative option")
    answers: dict[str, str] | None = Field(None, description="Answers to follow-up questions")
    feedback: str | None = Field(None, description="Optional user feedback")


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
    Generate multi-cloud architecture from requirements (NEW: Multi-stage wizard flow)

    NEW BEHAVIOR (Multi-Stage Wizard):
    This endpoint now starts a 5-stage interactive conversation:
    - Stage 1: Requirements Discovery (basic questions)
    - Stage 2: Compute & Scalability (recommendations with trade-offs)
    - Stage 3: Data Architecture (DB, storage decisions)
    - Stage 4: Security & Compliance (security decisions)
    - Stage 5: Final Review (cost summary, all decisions)
    
    Returns status="awaiting_stage_approval" with stage recommendations.
    Client must call /api/stage/approve to progress through stages.
    After Stage 5 approval, generates complete architecture.

    LEGACY BEHAVIOR (for backwards compatibility):
    Can still return status="needs_clarification" for single-round clarification.

    Args:
        request: GenerateRequest with user requirements

    Returns:
        OrchestratorOutput: Stage 1 questions OR clarification request OR complete architecture

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Get orchestrator instance
        orch = get_orchestrator()

        # NEW: Use stage-based workflow by default
        use_stage_based = True  # Can be made configurable via query param
        
        if use_stage_based:
            # NEW: Multi-stage wizard flow
            result = await orch.orchestrate_stage_based(request.requirements)
            
            # Store session data for stage progression
            if result.status == "awaiting_stage_approval" and result.session_id:
                sessions[result.session_id] = {
                    "user_input": request.requirements,
                    "initial_request": request.requirements,  # For compatibility with orchestrator
                    "conversation_stage": result.conversation_stage,
                    "stages_completed": result.stages_completed,
                    "all_stage_decisions": result.all_stage_decisions,
                    "requirements": result.requirements if result.requirements else {},
                    # Progressive multi-turn tracking
                    "question_round": 1,  # Start at Round 1
                    "previous_answers": {},  # All answers collected
                    "questions_asked": [],  # History of questions
                    "created_at": str(result.workflow_metadata.start_time),
                }
        else:
            # LEGACY: Old single-round clarification flow
            result = await orch.orchestrate(request.requirements)
            
            # If clarification needed, store session data
            if result.status == "needs_clarification" and result.session_id:
                sessions[result.session_id] = {
                    "partial_requirements": result.requirements,
                    "created_at": str(result.workflow_metadata.start_time),
                }

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


@app.post("/api/clarify", response_model=OrchestratorOutput, tags=["Architecture"])
async def submit_clarification(request: ClarificationRequest):
    """
    Submit answers to clarifying questions and continue workflow

    After receiving a NEEDS_CLARIFICATION response from /api/generate,
    use this endpoint to provide answers and continue architecture generation.

    Args:
        request: ClarificationRequest with session_id and answers

    Returns:
        OrchestratorOutput: Complete architecture with costs and documentation

    Raises:
        HTTPException: If session not found or generation fails
    """
    try:
        # Retrieve session data
        if request.session_id not in sessions:
            raise HTTPException(
                status_code=404, detail=f"Session not found: {request.session_id}"
            )

        session_data = sessions[request.session_id]

        # Get orchestrator instance
        orch = get_orchestrator()

        # Continue workflow with clarification answers
        result = await orch.continue_after_clarification(
            session_id=request.session_id,
            clarification_answers=request.answers,
            partial_requirements=session_data["partial_requirements"],
        )

        # Clean up session after successful completion
        if result.status == "success":
            del sessions[request.session_id]

        # Check for errors
        if result.status == "error":
            raise HTTPException(
                status_code=500,
                detail=result.error_message
                or "Architecture generation failed after clarification",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.post("/api/stage/approve", response_model=OrchestratorOutput, tags=["Architecture"])
async def approve_stage(request: StageApprovalRequest):
    """
    Submit approval/modification for a conversation stage (new multi-stage flow).
    
    Handles user response to stage recommendations:
    - approve: Move to next stage
    - modify: Ask for modifications
    - back: Go to previous stage
    - see_alternatives: Show alternative options
    
    After Stage 5 approval, generates complete architecture.
    
    Args:
        request: Stage approval with session_id, stage, action
        
    Returns:
        OrchestratorOutput: Next stage or final results
    """
    try:
        # Validate session exists
        if request.session_id not in sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {request.session_id}. It may have expired.",
            )
        
        session_data = sessions[request.session_id]
        
        # Import stage-related models
        from src.models.schemas import StageApprovalResponse, ConversationStage
        
        # Convert request to StageApprovalResponse
        stage_approval = StageApprovalResponse(
            session_id=request.session_id,
            stage=ConversationStage(request.stage),
            action=request.action,  # type: ignore
            modification_request=request.modification_request,
            selected_alternative=request.selected_alternative,
            answers=request.answers,
            feedback=request.feedback
        )
        
        # Handle Stage 1 multi-round flow
        if request.stage == "stage_1_requirements" and request.action == "approve":
            # Store answers from this round
            if request.answers:
                current_round = session_data.get("question_round", 1)
                
                # Store answers
                for question_text, answer in request.answers.items():
                    session_data["previous_answers"][question_text] = answer
                
                # Store questions asked (from result.current_stage_output.questions)
                # This will be populated by orchestrator
                
                logger.info(f"📝 Round {current_round}: Stored {len(request.answers)} answers")
        
        # Continue stage-based workflow
        orch = get_orchestrator()
        result = await orch.continue_stage_based(
            session_id=request.session_id,
            stage_approval=stage_approval,
            session_data=session_data
        )
        
        # Update session with latest state
        if result.status == "awaiting_stage_approval":
            # Check if still in Stage 1 (more rounds needed)
            if result.conversation_stage == ConversationStage.STAGE_1_REQUIREMENTS:
                # Still in Stage 1 - increment round
                current_round = session_data.get("question_round", 1)
                
                # Store questions asked in this round
                if result.stage_output and result.stage_output.questions:
                    for q in result.stage_output.questions:
                        session_data["questions_asked"].append(q.question)
                
                # Check if questions are empty (Stage 1 complete)
                if not result.stage_output.questions:
                    # Stage 1 complete - reset round counter for next stage
                    sessions[request.session_id].update({
                        "question_round": 1,
                        "stage1_complete": True,
                        "conversation_stage": result.conversation_stage,
                        "requirements": result.requirements if result.requirements else session_data.get("requirements", {}),
                        "updated_at": str(result.workflow_metadata.start_time)
                    })
                    logger.info("✅ Stage 1 complete - moving to Stage 2")
                else:
                    # More questions in Stage 1
                    sessions[request.session_id].update({
                        "question_round": current_round + 1,
                        "conversation_stage": result.conversation_stage,
                        "updated_at": str(result.workflow_metadata.start_time)
                    })
                    logger.info(f"🔄 Stage 1 continuing - Round {current_round + 1}")
            else:
                # Other stages - update normally
                sessions[request.session_id].update({
                    "stages_completed": result.stages_completed,
                    "all_stage_decisions": result.all_stage_decisions,
                    "conversation_stage": result.conversation_stage,
                    "updated_at": str(result.workflow_metadata.start_time),
                    # Preserve requirements if they exist in result
                    "requirements": result.requirements if result.requirements else session_data.get("requirements", {})
                })
        elif result.status == "success":
            # Workflow complete - clean up session
            sessions.pop(request.session_id, None)
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in stage approval: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ERROR in stage approval: {str(e)}")
        logger.error(f"Request details: session_id={request.session_id}, stage={request.stage}, action={request.action}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Stage approval failed: {str(e)}",
        )


# ============================================================================
# NEW: Knowledge Graph API Endpoints (Adaptive Requirements Gathering)
# ============================================================================

class KGStartRequest(BaseModel):
    """Request to start Knowledge Graph requirements gathering"""
    requirements: str = Field(
        ...,
        min_length=10,
        description="Initial user requirements in natural language"
    )


class KGAnswerRequest(BaseModel):
    """Request to submit answers for a specific domain"""
    session_id: str = Field(..., description="Session ID from KG start")
    domain: str = Field(..., description="Domain being answered (e.g., 'identity_access')")
    answers: Dict[str, Any] = Field(..., description="Answers as {field_name: value}")


class KGValidateRequest(BaseModel):
    """Request to validate if input is architecture-related"""
    requirements: str = Field(..., min_length=3, description="User input to validate")


class KGValidateResponse(BaseModel):
    """Response from validation check"""
    is_valid: bool = Field(..., description="True if request is cloud architecture related")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(..., description="Explanation of validation result")
    suggestion: str = Field(default="", description="Suggestion if invalid")


class KGArchitectureRequest(BaseModel):
    """Request to generate architecture from completed KG"""
    session_id: str = Field(..., description="Session ID with complete KG")


@app.post("/api/kg/validate", response_model=KGValidateResponse, tags=["Knowledge Graph"])
async def kg_validate(request: KGValidateRequest):
    """
    Pre-validate user input before starting requirements gathering.
    
    This prevents misuse by filtering out non-architecture requests like:
    - Unrelated topics (cooking, sports, general questions)
    - Malicious prompts
    - Empty or nonsensical input
    
    Returns:
        - is_valid: Whether the request is architecture-related
        - confidence: How confident the validation is (0.0-1.0)
        - reason: Explanation of the decision
        - suggestion: What to do if invalid
    """
    try:
        logger.info(f"🔍 Validating request: {request.requirements[:100]}...")
        
        orch = get_orchestrator()
        
        # Use a lightweight LLM call for validation
        validation_prompt = f"""You are a request validator for a cloud architecture design system.

Analyze this user request and determine if it's related to cloud architecture, cloud infrastructure, or software system design.

User Request: "{request.requirements}"

VALID requests include:
- Cloud architecture design (AWS, Azure, GCP, Oracle)
- Infrastructure requirements
- Application deployment needs
- System scalability/performance questions
- Security/compliance architecture
- Microservices, containers, serverless
- Database, storage, networking design
- CI/CD, DevOps, cloud migration

INVALID requests include:
- Cooking, recipes, food
- Sports, entertainment, general knowledge
- Personal advice, health, finance
- Homework help (non-technical)
- Malicious/harmful content
- Empty, nonsensical, or gibberish input

Respond ONLY with valid JSON in this exact format:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation",
  "suggestion": "If invalid, suggest what user should ask instead"
}}

Examples:
- "I want to make ice cream" → {{"is_valid": false, "confidence": 0.95, "reason": "Request is about cooking/food, not cloud architecture", "suggestion": "Try asking about cloud infrastructure, like 'Design an Azure web application' or 'Create an AWS microservices architecture'"}}
- "Design AKS cluster for e-commerce" → {{"is_valid": true, "confidence": 0.98, "reason": "Request is about Kubernetes cloud architecture", "suggestion": ""}}
- "asdfghjkl" → {{"is_valid": false, "confidence": 0.99, "reason": "Input appears to be gibberish", "suggestion": "Please provide a clear cloud architecture requirement"}}
"""

        # Quick LLM call (no Bing, no multi-agent)
        from src.services.openai_client import AzureOpenAIClient
        ai_client = AzureOpenAIClient()
        
        response_text = ai_client.generate_completion(
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0.1,  # Low temp for consistent validation
            max_tokens=300
        )
        
        # Parse JSON response
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        result = json.loads(response_text)
        
        logger.info(f"✅ Validation result: {result['is_valid']} (confidence: {result['confidence']})")
        
        return KGValidateResponse(
            is_valid=result["is_valid"],
            confidence=result["confidence"],
            reason=result["reason"],
            suggestion=result.get("suggestion", "")
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse validation response: {str(e)}")
        # Fail open - allow request if validation fails
        return KGValidateResponse(
            is_valid=True,
            confidence=0.5,
            reason="Validation check failed, proceeding with request",
            suggestion=""
        )
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}\n{traceback.format_exc()}")
        # Fail open - allow request if validation fails
        return KGValidateResponse(
            is_valid=True,
            confidence=0.5,
            reason="Validation service unavailable, proceeding with request",
            suggestion=""
        )


@app.post("/api/kg/start", tags=["Knowledge Graph"])
async def kg_start(request: KGStartRequest):
    """
    Start Knowledge Graph requirements gathering (ADAPTIVE approach).
    
    This replaces the fixed 3-round wizard with intelligent domain-based questioning.
    
    Returns:
        - status: "needs_clarification" (with questions) or "complete"
        - domain: Current domain being questioned
        - questions: List of questions for this domain
        - domain_confidence: Confidence scores for all 6 domains
    """
    try:
        logger.info(f"🌐 Starting KG requirements gathering: {request.requirements[:100]}...")
        
        orch = get_orchestrator()
        
        # Start KG orchestration
        result = await orch._execute_requirements_stage_with_kg(
            user_input=request.requirements,
            session_data=None  # New session
        )
        
        # Create session
        import uuid
        session_id = str(uuid.uuid4())
        
        sessions[session_id] = {
            "kg": result["kg"],
            "requirements": request.requirements,
            "created_at": str(datetime.now()),
            "workflow_type": "knowledge_graph"
        }
        
        logger.info(f"✅ KG session created: {session_id}")
        logger.info(f"📊 Status: {result['status']}, Domain: {result.get('domain', 'N/A')}")
        
        domain_conf = result.get("domain_confidence", {})
        logger.info(f"📊 Domain confidence from orchestrator: {domain_conf}")
        
        return {
            "session_id": session_id,
            "status": result["status"],
            "domain": result.get("domain"),
            "questions": result.get("questions", []),
            "ready_for_design": result.get("ready_for_design", False),
            "critical_gaps": result.get("critical_gaps", 0),
            "conflicts": result.get("conflicts", 0),
            "domain_confidence": domain_conf,
            "overall_confidence": result.get("confidence", 0.0),
        }
        
    except Exception as e:
        logger.error(f"❌ KG start failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"KG start failed: {str(e)}")


@app.post("/api/kg/answer", tags=["Knowledge Graph"])
async def kg_answer(request: KGAnswerRequest):
    """
    Submit answers for a specific domain and get next questions.
    
    The orchestrator will:
    1. Update the Knowledge Graph with answers
    2. Recalculate confidence for this domain
    3. Detect conflicts
    4. Return next questions OR ready_for_design = True
    """
    try:
        # Validate session
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")
        
        session_data = sessions[request.session_id]
        
        logger.info(f"📝 Processing answers for domain: {request.domain}")
        
        orch = get_orchestrator()
        
        # Process answers
        result = orch.process_kg_answers(
            domain=request.domain,
            answers=request.answers,
            session_data=session_data
        )
        
        # Update session
        sessions[request.session_id]["kg"] = result["kg"]
        
        logger.info(f"✅ KG updated - Status: {result['status']}")
        
        domain_conf = result.get("domain_confidence", {})
        logger.info(f"📊 Domain confidence from orchestrator: {domain_conf}")
        
        return {
            "session_id": request.session_id,
            "status": result["status"],
            "domain": result.get("domain"),
            "questions": result.get("questions", []),
            "ready_for_design": result.get("ready_for_design", False),
            "critical_gaps": result.get("critical_gaps", 0),
            "conflicts": result.get("conflicts", 0),
            "domain_confidence": domain_conf,
            "overall_confidence": result.get("confidence", 0.0),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ KG answer failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"KG answer failed: {str(e)}")


@app.get("/api/kg/status/{session_id}", tags=["Knowledge Graph"])
async def kg_status(session_id: str):
    """
    Get current Knowledge Graph status.
    
    Returns:
        - ready_for_design: Whether KG is complete
        - domain_confidence: Confidence scores for all domains
        - critical_gaps: Number of remaining critical gaps
        - conflicts: Number of unresolved conflicts
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        
        session_data = sessions[session_id]
        kg = session_data.get("kg")
        
        if not kg:
            raise HTTPException(status_code=400, detail="No Knowledge Graph in session")
        
        return {
            "session_id": session_id,
            "ready_for_design": kg.status.ready_for_design,
            "critical_gaps": len(kg.status.critical_gaps),
            "conflicts": len(kg.status.conflicts),
            "domain_confidence": {
                "identity": kg.identity_access.confidence,
                "runtime": kg.runtime_platform.confidence,
                "networking": kg.networking_connectivity.confidence,
                "data": kg.data_persistence.confidence,
                "resiliency": kg.resiliency_dr.confidence,
                "monitoring": kg.monitoring_observability.confidence,
                "security": kg.security_governance.confidence,
            },
            "conflicts_detail": [
                {
                    "id": c.conflict_id,
                    "domains": c.domains_involved,
                    "description": c.description,
                    "severity": c.severity,
                }
                for c in kg.status.conflicts
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ KG status failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"KG status failed: {str(e)}")


@app.post("/api/kg/architecture", tags=["Knowledge Graph"])
async def kg_generate_architecture(request: KGArchitectureRequest):
    """
    Generate architecture from a completed Knowledge Graph.
    
    This endpoint calls the Architecture Agent with KG input.
    
    Returns:
        Complete architecture design (same format as /api/generate)
    """
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")
        
        session_data = sessions[request.session_id]
        kg = session_data.get("kg")
        
        if not kg:
            raise HTTPException(status_code=400, detail="No Knowledge Graph in session")
        
        # Debug: Show readiness status
        logger.info(f"🔍 KG Status Check:")
        logger.info(f"  - ready_for_design: {kg.status.ready_for_design}")
        logger.info(f"  - critical_gaps: {len(kg.status.critical_gaps)}")
        logger.info(f"  - total_conflicts: {len(kg.status.conflicts)}")
        critical_conflicts = [c for c in kg.status.conflicts if c.severity == "critical"]
        logger.info(f"  - critical_conflicts: {len(critical_conflicts)}")
        
        # List all critical conflicts
        for c in critical_conflicts:
            logger.info(f"    ❌ CRITICAL: {c.conflict_id} - {c.description[:100]}...")
        
        if not kg.status.ready_for_design:
            raise HTTPException(
                status_code=400,
                detail=f"Knowledge Graph not ready for design. "
                       f"Critical gaps: {len(kg.status.critical_gaps)}, "
                       f"Conflicts: {len(kg.status.conflicts)} ({len(critical_conflicts)} critical)"
            )
        
        logger.info(f"🏗️ Generating architecture from KG (session: {request.session_id})")
        
        orch = get_orchestrator()
        
        # Generate architecture from KG
        architecture = await orch._execute_architecture_stage_from_kg(kg)
        
        logger.info(f"✅ Architecture generated: {len(architecture.services)} services")
        
        # Convert KG to RequirementsOutput (needed for cost & doc stages)
        requirements = orch.architecture_agent._convert_kg_to_requirements(kg)
        
        # Continue with Cost stage
        logger.info("💰 Running Cost Estimation stage...")
        cost_output = await orch._execute_cost_stage(requirements, architecture)
        logger.info(f"✅ Cost estimation complete: ${cost_output.total_monthly_cost_medium}/month")
        
        # Continue with Documentation stage
        logger.info("📝 Running Documentation stage...")
        documentation = await orch._execute_documentation_stage(requirements, architecture, cost_output)
        logger.info(f"✅ Documentation complete: HLD generated ({len(documentation.content)} chars)")
        
        return {
            "session_id": request.session_id,
            "status": "success",
            "architecture": architecture.model_dump(),
            "cost_estimate": cost_output.model_dump(),
            "documentation": documentation.model_dump(),
            "message": "Complete solution design generated successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ KG architecture generation failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Architecture generation failed: {str(e)}")


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
            "generate": "/api/generate (POST) - Legacy wizard",
            "kg_start": "/api/kg/start (POST) - NEW: Start adaptive KG gathering",
            "kg_answer": "/api/kg/answer (POST) - NEW: Submit domain answers",
            "kg_status": "/api/kg/status/{session_id} (GET) - NEW: Get KG status",
            "kg_architecture": "/api/kg/architecture (POST) - NEW: Generate from KG",
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
