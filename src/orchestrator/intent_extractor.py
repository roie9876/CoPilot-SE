"""
Intent & Context Extractor

Analyzes natural language user input and extracts:
- User intent (new_deployment, extend_existing, dr_only, migration, optimize_security, optimize_cost)
- Cloud provider (always Azure for POC)
- Workload type (web_app, api, mobile_backend, data_analytics, etc.)
- Initial facts from user description
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent, AgentThread
from azure.identity import DefaultAzureCredential

from src.models.knowledge_graph import (
    Intent,
    CloudProvider,
    WorkloadType,
    Context,
    KnowledgeGraph,
)


class IntentExtractor:
    """
    Extracts user intent and initial context from natural language input.
    Uses Azure AI Agent Service with GPT-5 for structured extraction.
    """

    def __init__(self):
        """Initialize the Intent Extractor with Azure AI Agents Service."""
        self.logger = logging.getLogger(__name__)
        self.use_mock = self._should_use_mock_mode()

        if self.use_mock:
            self.logger.info("IntentExtractor running in mock mode. Azure AI Agent calls are disabled.")
            self.azure_endpoint = None
            self.model_deployment = None
            self.credential = None
            self.agents_client = None
            self.agent = None
            return

        # Get Azure AI Foundry Project endpoint (required for Agents API)
        self.azure_endpoint = os.getenv("AZURE_AI_PROJECT")
        self.model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        if not self.azure_endpoint:
            raise ValueError("AZURE_AI_PROJECT environment variable is required for Azure AI Agents")

        # Initialize Azure AI Agents Client with AI Foundry endpoint
        self.credential = DefaultAzureCredential()
        self.agents_client = AgentsClient(
            endpoint=self.azure_endpoint,
            credential=self.credential
        )

        # Create the intent extraction agent
        self.agent = self._create_agent()

    def _should_use_mock_mode(self) -> bool:
        """Determine whether to bypass Azure Agents (used for tests/offline runs)."""
        mock_flag = os.getenv("DISABLE_AZURE_AGENTS", "").strip().lower() in {"1", "true", "yes"}
        if mock_flag:
            return True
        required = ["AZURE_AI_PROJECT", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            logging.getLogger(__name__).warning(
                "Missing Azure configuration %s; falling back to mock intent extraction.", missing
            )
            return True
        return False

    def _create_agent(self) -> Agent:
        """Create the intent extraction agent with specialized instructions."""
        instructions = """You are an expert at analyzing user requirements for cloud architecture projects.

Your task is to extract structured information from user input:

1. **Intent Classification** - Classify the user's primary intent:
   - new_deployment: Building something new from scratch (greenfield)
   - extend_existing: Adding to existing infrastructure (brownfield)
   - dr_only: Disaster recovery or backup solution
   - migration: Migrating from on-premises or another cloud
   - optimize_security: Improving security posture
   - optimize_cost: Cost reduction focus

2. **Cloud Provider Detection** - Always Azure:
   - azure: Microsoft Azure (this is an Azure-only solution)
   Look for Azure service mentions to understand customer's familiarity with Azure

3. **Workload Type** - Identify the application type:
   - web_app: Web application or website
   - api: REST API or microservices
   - mobile_backend: Mobile app backend
   - data_pipeline: Data processing/analytics
   - ml_service: Machine learning workload
   - batch_job: Batch jobs
   - microservices: Microservices architecture
   - iot: IoT application
   - e_commerce: E-commerce platform
   - other: Other workload types
   - unknown: Cannot determine workload type

4. **Business Description** - Extract key facts:
   - What problem are they solving?
   - What services/technologies did they mention?
   - Any specific requirements (users, scale, regions)?
   - Any constraints mentioned?

**CRITICAL**: Return ONLY valid JSON in this exact format:
{
  "intent": "new_deployment",
  "cloud_provider": "azure",
  "workload_type": "web_app",
  "business_description": "User wants to build...",
  "confidence": 0.85
}

If information is ambiguous, use:
- intent: "new_deployment" (default)
- cloud_provider: "azure" (default)
- workload_type: "web_app" (default)
- Lower confidence score (0.5-0.7)
"""

        agent = self.agents_client.create_agent(
            model=self.model_deployment,
            name="Intent Extractor",
            instructions=instructions,
            temperature=0.1,  # Low temperature for consistent extraction
        )
        return agent

    def extract(self, user_input: str) -> Context:
        """
        Extract intent and context from user input.

        Args:
            user_input: Natural language description from user

        Returns:
            Context object with extracted information

        Raises:
            ValueError: If input is empty or extraction fails
        """
        if not user_input or not user_input.strip():
            raise ValueError("User input cannot be empty")

        if self.use_mock:
            return self._mock_extract(user_input)

        try:
            # Create thread and run the agent - this returns a streaming response
            result = self.agents_client.create_thread_and_process_run(
                agent_id=self.agent.id,
                thread={
                    "messages": [{
                        "role": "user",
                        "content": f"Extract intent and context from this user input:\n\n{user_input}"
                    }]
                }
            )

            # The result from create_thread_and_process_run is already processed
            # Extract the response text directly from the result
            response_text = ""
            
            # The SDK processes the run and returns the result
            # We need to get the last message from the completed run
            # For now, we'll use the Azure OpenAI client directly as a fallback
            from openai import AzureOpenAI
            
            openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            openai_client = AzureOpenAI(
                azure_endpoint=openai_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            # Use completion API directly
            completion = openai_client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": self.agent.instructions},
                    {"role": "user", "content": f"Extract intent and context from this user input:\n\n{user_input}"}
                ],
                temperature=0.3
            )
            
            response_text = completion.choices[0].message.content

            if not response_text:
                raise RuntimeError("No response from intent extraction agent")

            # Parse the JSON response
            try:
                extracted_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re

                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(1))
                else:
                    raise ValueError(f"Failed to parse JSON from response: {response_text}")

            # Map string values to enums
            intent = Intent(extracted_data.get("intent", "new_deployment"))
            cloud_provider = CloudProvider(extracted_data.get("cloud_provider", "azure"))
            workload_type = WorkloadType(extracted_data.get("workload_type", "web_app"))

            # Create Context object
            context = Context(
                intent=intent,
                cloud_provider=cloud_provider,
                workload_type=workload_type,
                business_description=extracted_data.get("business_description", user_input),
            )

            return context

        except Exception as e:
            raise RuntimeError(f"Intent extraction failed: {str(e)}")

    def extract_initial_facts(
        self, user_input: str, context: Context
    ) -> Dict[str, Any]:
        """
        Extract additional initial facts from user input to pre-populate knowledge graph.

        This is optional but helps reduce questions by capturing obvious information.

        Args:
            user_input: Natural language description
            context: Already extracted context

        Returns:
            Dictionary of domain fields to pre-populate
        """
        if self.use_mock:
            return self._mock_initial_facts(user_input)

        try:
            prompt = f"""Given this user input and context, extract specific technical facts:

User Input: {user_input}
Intent: {context.intent.value}
Cloud Provider: {context.cloud_provider.value}
Workload Type: {context.workload_type.value}

Extract ONLY facts explicitly mentioned (don't infer or assume):

1. **Identity & Access**:
   - Is Azure AD/Entra ID mentioned?
   - Expected user count?
   - MFA mentioned?
   - Authentication type (internal employees, external customers)?

2. **Runtime Platform**:
   - Specific services mentioned (AKS, App Service, Functions, VMs)?
   - Containerized? (Docker, Kubernetes mentioned?)
   - Specific runtimes (.NET, Java, Python, Node.js)?

3. **Networking**:
   - Public or private exposure?
   - Specific regions mentioned?
   - VPN or private connectivity mentioned?

4. **Data Persistence**:
   - Database engines mentioned (SQL, PostgreSQL, Cosmos DB)?
   - Data volume/size mentioned?
   - PII or sensitive data mentioned?

5. **Resiliency**:
   - Multi-region mentioned?
   - HA/DR requirements?
   - RTO/RPO values?

6. **Security & Governance**:
   - Compliance frameworks (HIPAA, PCI-DSS, GDPR, SOC2)?
   - Encryption requirements?

Return ONLY valid JSON:
{{
  "identity_access": {{"auth_users": 1000, "mfa_policy": "required"}},
  "runtime_platform": {{"target_runtime": "aks", "containerized": true}},
  "networking_connectivity": {{"exposure": "public", "regions_in_scope": ["swedencentral"]}},
  "data_persistence": {{"primary_db_engine": "azure_sql"}},
  "resiliency_dr": {{"multi_region": false}},
  "security_governance": {{"compliance_frameworks": ["gdpr"]}}
}}

If nothing is mentioned for a section, return empty object {{}}.
"""

            # Run the agent with the prompt - using OpenAI client fallback
            from openai import AzureOpenAI
            
            openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            openai_client = AzureOpenAI(
                azure_endpoint=openai_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            # Use completion API directly
            completion = openai_client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": self.agent.instructions},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            response_text = completion.choices[0].message.content
            
            if not response_text:
                return {}

            try:
                facts = json.loads(response_text)
                return facts
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                import re

                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                return {}

        except Exception:
            # Fact extraction is optional - don't fail the whole process
            return {}

    def __del__(self):
        """Cleanup: Delete the agent when extractor is destroyed."""
        try:
            if hasattr(self, "agent") and self.agent:
                self.agents_client.delete_agent(self.agent.id)
        except Exception:
            pass  # Ignore cleanup errors

    # ------------------------------------------------------------------
    # Mock helpers (used during tests/offline runs)
    # ------------------------------------------------------------------
    def _mock_extract(self, user_input: str) -> Context:
        """Lightweight deterministic extractor for offline/testing use."""
        lowered = user_input.lower()

        intent = "new_deployment"
        if "disaster" in lowered or "dr" in lowered:
            intent = "dr_only"
        elif "migrate" in lowered or "migration" in lowered:
            intent = "migration"
        elif "optimize cost" in lowered or "cost" in lowered:
            intent = "optimize_cost"
        elif "security" in lowered:
            intent = "optimize_security"

        workload = "web_app"
        if "api" in lowered:
            workload = "api"
        elif "mobile" in lowered:
            workload = "mobile_backend"
        elif "aks" in lowered or "microservice" in lowered or "container" in lowered:
            workload = "microservices"
        elif "data" in lowered or "analytics" in lowered:
            workload = "data_pipeline"

        context = Context(
            intent=Intent(intent),
            cloud_provider=CloudProvider("azure"),
            workload_type=WorkloadType(workload),
            business_description=user_input.strip(),
        )
        return context

    def _mock_initial_facts(self, user_input: str) -> Dict[str, Any]:
        """Return heuristic facts without calling Azure services."""
        facts: Dict[str, Any] = {
            "identity_access": {},
            "runtime_platform": {},
            "networking_connectivity": {},
            "data_persistence": {},
            "resiliency_dr": {},
            "security_governance": {},
        }

        lowered = user_input.lower()

        if "azure ad" in lowered or "entra" in lowered:
            facts["identity_access"]["auth_provider"] = "entra_id"
        if "mfa" in lowered:
            facts["identity_access"]["mfa_policy"] = "required"

        if "aks" in lowered:
            facts["runtime_platform"]["target_runtime"] = "aks"
            facts["runtime_platform"]["containerized"] = True
        elif "app service" in lowered:
            facts["runtime_platform"]["target_runtime"] = "app_service"
        elif "functions" in lowered:
            facts["runtime_platform"]["target_runtime"] = "functions"

        if "private" in lowered:
            facts["networking_connectivity"]["exposure"] = "private"
        elif "public" in lowered or "internet" in lowered:
            facts["networking_connectivity"]["exposure"] = "public"

        if "sql" in lowered:
            facts["data_persistence"]["primary_db_engine"] = "azure_sql"
        elif "cosmos" in lowered:
            facts["data_persistence"]["primary_db_engine"] = "cosmos_db"

        if "multi-region" in lowered or "multi region" in lowered:
            facts["resiliency_dr"]["multi_region"] = True
        if "rpo" in lowered or "rto" in lowered or "dr" in lowered:
            facts["resiliency_dr"]["dr_focus"] = True

        if "pci" in lowered or "gdpr" in lowered or "hipaa" in lowered:
            frameworks = facts["security_governance"].setdefault("compliance_frameworks", [])
            if "pci" in lowered:
                frameworks.append("pci")
            if "gdpr" in lowered:
                frameworks.append("gdpr")
            if "hipaa" in lowered:
                frameworks.append("hipaa")

        return {k: v for k, v in facts.items() if v}
