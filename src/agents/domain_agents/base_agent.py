"""
Base Domain Agent - Abstract class for all domain-specific agents.

All domain agents (Identity, Runtime, Networking, Data, Resiliency, Security)
inherit from this base class and implement the core contract:

1. get_missing_critical_fields() - Identify what's still unknown
2. generate_questions() - Create questions for missing fields
3. detect_conflicts() - Find contradictions with other domains
4. update_confidence() - Calculate confidence score for this domain

Design Principles:
- Each agent is a specialist in ONE domain
- Agents only ask about CRITICAL missing information
- Agents explicitly detect conflicts (not assumptions)
- Confidence scores reflect completeness
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.knowledge_graph import KnowledgeGraph, Conflict
import logging
import json


class DomainAgentQuestion(Dict[str, Any]):
    """
    Structured question from a domain agent.
    
    Fields:
    - question: The actual question text
    - field: Which Knowledge Graph field this updates
    - type: "boolean" | "choice" | "text" | "number"
    - options: List of choices (if type = "choice")
    - critical: Is this field critical before design?
    - rationale: Why this question matters
    - domain: Which domain this belongs to
    """
    pass


class BaseDomainAgent(ABC):
    """
    Abstract base class for all domain agents.
    
    Each domain agent:
    1. Owns a section of the Knowledge Graph
    2. Knows which fields are CRITICAL vs nice-to-have
    3. Generates adaptive questions (only asks what's missing)
    4. Detects conflicts with other domains
    5. Updates confidence scores
    """
    
    def __init__(self, domain_name: str):
        """
        Initialize domain agent.
        
        Args:
            domain_name: Name of the domain (e.g., "identity_access", "runtime_platform")
        """
        self.domain_name = domain_name
        self.logger = logging.getLogger(f"{__name__}.{domain_name}")
        
        # Each agent defines which fields are CRITICAL
        # (must be known before architecture generation)
        self.critical_fields: List[str] = []
        
        # Nice-to-have fields (improve design but not required)
        self.optional_fields: List[str] = []
    
    @abstractmethod
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify which CRITICAL fields in this domain are still missing.
        
        This method examines the Knowledge Graph and returns a list of
        field names that are:
        1. Critical for this domain
        2. Currently None or unknown
        3. Relevant to the user's intent
        
        Example:
            For IdentityAgent:
            - If existing_tenant is None → missing
            - If auth_users is None → missing
            - If mfa_policy is None AND no compliance requirements → NOT missing
        
        Args:
            graph: Current state of the Knowledge Graph
        
        Returns:
            List of field names still missing (e.g., ["existing_tenant", "auth_users"])
        """
        pass
    
    def get_all_missing_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Get ALL missing fields (both critical AND optional) for low-confidence domains.
        
        This is used when a domain's confidence is < 0.8 and we need to ask
        additional questions to boost confidence, even if all critical fields are filled.
        
        Default implementation: Check all fields in the domain object for None values.
        Subclasses can override for more sophisticated logic.
        
        Args:
            graph: Current state of the Knowledge Graph
        
        Returns:
            List of ALL field names that are None or need clarification
        """
        domain_obj = getattr(graph, self.domain_name)
        missing = []
        
        # Check all fields defined in critical_fields and optional_fields
        all_fields = self.critical_fields + self.optional_fields
        
        for field_name in all_fields:
            if hasattr(domain_obj, field_name):
                value = getattr(domain_obj, field_name)
                # Consider None, empty string, or empty list as missing
                if value is None or value == "" or value == []:
                    missing.append(field_name)
        
        return missing
    
    @abstractmethod
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate questions for missing critical fields.
        
        Questions should be:
        1. Clear and specific
        2. Include rationale (why this matters)
        3. Provide options for choice questions
        4. Mark critical vs optional
        
        Args:
            missing_fields: List of field names to ask about
            graph: Current Knowledge Graph (for context)
        
        Returns:
            List of structured questions
        """
        pass
    
    @abstractmethod
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect contradictions between this domain and others.
        
        Example conflicts:
        - NetworkingAgent: exposure = "private_only"
          BUT RuntimeAgent: aks_ingress_model = "public_lb"
        - ResiliencyAgent: multi_region = True
          BUT DataAgent: can_replicate_data_cross_region = False
        
        Conflicts should:
        1. Describe the contradiction clearly
        2. Include which domains are involved
        3. Provide a clarification question
        4. Have severity level (critical/high/medium/low)
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            List of detected conflicts
        """
        pass
    
    def update_confidence(self, graph: KnowledgeGraph) -> float:
        """
        Calculate confidence score for this domain (0.0 to 1.0).
        
        Confidence formula:
        - Start with 0.0
        - Add points for each critical field filled
        - Add points for each optional field filled
        - Weighted: Critical fields worth more
        
        Example:
            3 critical fields, 2 optional fields
            2 critical filled, 1 optional filled
            
            Confidence = (2/3 * 0.8) + (1/2 * 0.2) = 0.53 + 0.10 = 0.63
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            Confidence score (0.0 = no info, 1.0 = complete)
        """
        domain_section = self._get_domain_section(graph)
        if not domain_section:
            return 0.0
        
        # Count filled critical fields
        critical_filled = 0
        for field in self.critical_fields:
            value = getattr(domain_section, field, None)
            if value is not None and value != [] and value != "":
                critical_filled += 1
        
        # Count filled optional fields
        optional_filled = 0
        for field in self.optional_fields:
            value = getattr(domain_section, field, None)
            if value is not None and value != [] and value != "":
                optional_filled += 1
        
        # Weighted average (80% critical, 20% optional)
        critical_score = (
            (critical_filled / len(self.critical_fields))
            if self.critical_fields else 0.0
        )
        optional_score = (
            (optional_filled / len(self.optional_fields))
            if self.optional_fields else 0.0
        )
        
        confidence = (critical_score * 0.8) + (optional_score * 0.2)
        
        # Update the graph
        if hasattr(domain_section, "confidence"):
            domain_section.confidence = confidence
        
        return confidence
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Determine if this domain is relevant for the user's intent.
        
        Example:
            - DR-only intent → ResiliencyAgent is highly relevant
            - New deployment → All agents relevant
            - Optimize cost → SecurityAgent less relevant
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            True if this domain should be consulted
        """
        # By default, all domains are relevant
        # Subclasses can override for intent-specific logic
        return True
    
    def _get_domain_section(self, graph: KnowledgeGraph):
        """
        Get this agent's section from the Knowledge Graph.
        
        Args:
            graph: Knowledge Graph
        
        Returns:
            Domain section object (e.g., graph.identity_access)
        """
        return getattr(graph, self.domain_name, None)
    
    def _is_field_filled(self, domain_section, field_name: str) -> bool:
        """
        Check if a field has a meaningful value.
        
        Args:
            domain_section: Domain object (e.g., IdentityAccess)
            field_name: Field to check
        
        Returns:
            True if field is filled with meaningful data
        """
        value = getattr(domain_section, field_name, None)
        
        # Check for None, empty string, empty list
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        if isinstance(value, str) and value.lower() in ["unknown", "not_specified"]:
            return False
        
        return True
    
    def search_domain_knowledge(
        self,
        user_context: str,
        missing_fields: List[str],
        cloud_platform: str = "azure"
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: This method is no longer used.
        
        Azure AI Agent Service with Bing Grounding automatically searches
        Microsoft documentation. No need for manual Bing Search API calls.
        
        Args:
            user_context: Original user request (e.g., "IoT app 10K devices")
            missing_fields: Fields we need to ask about
            cloud_platform: Cloud platform (default: azure)
        
        Returns:
            Empty list (method deprecated)
        """
        # This method is deprecated - Azure AI Agent handles Bing search automatically
        return []
    
    def generate_expert_system_prompt(self) -> str:
        """
        Generate domain-specific expert system prompt for LLM.
        
        This method returns a prompt that establishes the LLM as an expert
        in this specific domain. Subclasses should override to provide
        domain-specific expertise.
        
        Returns:
            Expert system prompt string
        """
        # Default generic prompt
        return f"""You are an expert Microsoft Azure architect specializing in {self.domain_name.replace('_', ' ')}.
        
Your role is to generate contextual, relevant questions to gather missing architectural requirements.

Core principles:
1. Ask ONLY about information relevant to the user's scenario
2. Reference official Microsoft documentation and best practices
3. Explain WHY each question matters (provide context)
4. Provide clear options with explanations
5. Cite sources (Microsoft Learn, Well-Architected Framework)

Do NOT ask about:
- Technologies the user didn't mention
- Irrelevant platforms (e.g., don't ask about Kubernetes if user wants VMs)
- Already-answered questions

Your questions should educate the user while gathering requirements."""
    
    def generate_contextual_questions_with_llm(
        self,
        graph: KnowledgeGraph,
        missing_fields: List[str]
    ) -> List[DomainAgentQuestion]:
        """
        Generate contextual questions using LLM + domain knowledge retrieval.
        
        This replaces hardcoded question templates with AI-powered generation
        that considers:
        1. User's original request
        2. Current Knowledge Graph state
        3. Microsoft documentation (via Bing Search)
        4. Domain expertise
        
        Args:
            graph: Current Knowledge Graph
            missing_fields: Fields that need to be filled
        
        Returns:
            List of expert, contextual questions
        """
        if not missing_fields:
            return []
        
        try:
            # Use Agent Framework Client with Bing Grounding
            from src.services.agent_framework_client import AgentFrameworkClient
            
            agent_framework = AgentFrameworkClient()
            
            # Extract user context
            user_original_request = graph.context.given_input_raw or "cloud architecture"
            workload_type = getattr(graph.context, "workload_type", "general")
            intent = getattr(graph.context, "intent", "NEW_DEPLOYMENT")
            
            self.logger.info(f"Creating Agent Framework agent for {self.domain_name} with Bing search...")
            
            # Get domain-specific expert system prompt
            expert_instructions = self.generate_expert_system_prompt()
            
            # Build full instructions for the agent
            full_instructions = f"""{expert_instructions}

You will receive a user request and missing fields. Your task is to generate 2-4 expert questions.

CRITICAL RULES:
1. Use Bing Search to find relevant Microsoft Azure documentation
2. Ask ONLY about information relevant to the user's actual scenario
3. NEVER ask yes/no questions - always provide specific options (e.g., "containers" vs "VMs", not "yes" vs "no")
4. Context awareness:
   - If user mentioned VMs → Ask about VM sizing, OS, disk types (NOT Kubernetes/AKS CNI)
   - If user mentioned AKS/containers → Ask about CNI plugins, node pools (NOT VM management)
   - If user mentioned serverless → Ask about Functions, Logic Apps (NOT VMs or containers)
   - If user mentioned IoT → Ask about IoT Edge, device management (NOT web app features)
5. Technology-specific questions:
   - Azure CNI plugin is ONLY for AKS (Kubernetes networking), NOT for standalone VMs
   - VM Scale Sets are for VMs, NOT for containers
   - Container networking uses Azure CNI in AKS, NOT VNet integration
6. Reference Microsoft Learn documentation you find via Bing
7. Explain WHY each question matters (business impact)
8. Provide 2-4 clear options with trade-offs and recommendations

Return VALID JSON array only (no markdown, no extra text):
[
  {{
    "question": "Clear question text with **bold** options",
    "field": "field_name_from_missing_fields",
    "type": "choice",
    "options": [
      {{
        "value": "option_value",
        "label": "Option Label",
        "explanation": "Why choose this option"
      }}
    ],
    "critical": true,
    "rationale": "Why this question matters (cite Microsoft docs)",
    "source": "URL from Microsoft documentation",
    "domain": "{self.domain_name}"
  }}
]
"""
            
            # Create ChatAgent with Bing enabled
            agent = agent_framework.create_agent(
                name=f"{self.domain_name}_questions",
                instructions=full_instructions,
                enable_bing=True  # Enable Bing web search
            )
            
            # Build prompt for this specific request
            prompt = f"""USER REQUEST: "{user_original_request}"
WORKLOAD TYPE: {workload_type}
INTENT: {intent}

MISSING FIELDS TO ASK ABOUT:
{', '.join(missing_fields)}

CURRENT KNOWLEDGE GRAPH STATE:
{self._summarize_graph_for_llm(graph)}

Generate 2-4 expert questions to gather the missing information. Use Bing to search for Microsoft Azure best practices."""
            
            # Run agent synchronously (Agent Framework will handle async internally)
            self.logger.info(f"Running Agent Framework agent for {self.domain_name}...")
            import asyncio
            
            # Run in async context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = executor.submit(asyncio.run, agent.run(prompt)).result()
            else:
                result = asyncio.run(agent.run(prompt))
            
            # Extract response text
            if not result or not result.messages:
                raise ValueError("Agent returned empty response")
            
            response_text = result.messages[-1].text
            self.logger.info(f"Agent response received ({len(response_text)} chars)")
            
            # Parse JSON response from agent
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Extract JSON from markdown
                lines = response_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or not line.startswith("```"):
                        json_lines.append(line)
                response_text = "\n".join(json_lines)
            
            questions = json.loads(response_text)
            
            # Validate and convert to DomainAgentQuestion
            validated_questions = []
            for q in questions:
                if isinstance(q, dict) and "question" in q and "field" in q:
                    # Ensure domain is set
                    q["domain"] = self.domain_name
                    
                    # Flatten options: convert [{value, label, explanation}] to [value1, value2, ...]
                    if "options" in q and isinstance(q["options"], list):
                        flattened_options = []
                        for opt in q["options"]:
                            if isinstance(opt, dict) and "value" in opt:
                                # Extract just the value from the object
                                flattened_options.append(opt["value"])
                            elif isinstance(opt, str):
                                # Already a string, keep it
                                flattened_options.append(opt)
                        q["options"] = flattened_options
                    
                    validated_questions.append(DomainAgentQuestion(q))
            
            self.logger.info(
                f"✅ Generated {len(validated_questions)} LLM-POWERED questions for {self.domain_name}"
            )
            # Log questions (using dict access since DomainAgentQuestion is a Dict)
            question_texts = [q.get("question", "")[:50] + "..." if len(q.get("question", "")) > 50 else q.get("question", "") for q in validated_questions]
            self.logger.info(f"   Questions: {question_texts}")
            
            return validated_questions
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}")
            self.logger.error(f"Response was: {response_text[:500]}")
            # Fallback to hardcoded templates
            return self._fallback_to_template_questions(graph, missing_fields)
            
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to generate contextual questions: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to hardcoded templates
            return self._fallback_to_template_questions(graph, missing_fields)
    
    def _summarize_graph_for_llm(self, graph: KnowledgeGraph) -> str:
        """
        Create a concise summary of the Knowledge Graph for LLM context.
        Includes cross-domain context to avoid irrelevant questions.
        
        Args:
            graph: Knowledge Graph
        
        Returns:
            Summary string with current domain + key cross-domain facts
        """
        summary_lines = []
        
        # Add critical cross-domain context (helps avoid irrelevant questions)
        if hasattr(graph, 'runtime_platform') and graph.runtime_platform:
            rt = graph.runtime_platform
            if hasattr(rt, 'primary_platform') and rt.primary_platform:
                summary_lines.append(f"PLATFORM CHOICE: {rt.primary_platform}")
            if hasattr(rt, 'containerized') and rt.containerized:
                summary_lines.append(f"CONTAINERIZED: {rt.containerized}")
        
        # Add current domain's filled fields
        domain_section = self._get_domain_section(graph)
        if domain_section:
            summary_lines.append(f"\n{self.domain_name.upper()} DOMAIN:")
            for field in self.critical_fields + self.optional_fields:
                if self._is_field_filled(domain_section, field):
                    value = getattr(domain_section, field, None)
                    summary_lines.append(f"- {field}: {value}")
        
        if len(summary_lines) > 0:
            return "\n".join(summary_lines)
        else:
            return "No information yet."
    
    def _fallback_to_template_questions(
        self,
        graph: KnowledgeGraph,
        missing_fields: List[str]
    ) -> List[DomainAgentQuestion]:
        """
        Fallback to hardcoded template questions if LLM fails.
        
        Subclasses should override this with their legacy template logic.
        
        Args:
            graph: Knowledge Graph
            missing_fields: Missing fields
        
        Returns:
            List of template-based questions
        """
        self.logger.warning(
            f"Using fallback template questions for {self.domain_name}"
        )
        # Default: return empty (subclasses override with templates)
        return []
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(domain='{self.domain_name}')"
