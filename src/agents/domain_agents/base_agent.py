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
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(domain='{self.domain_name}')"
