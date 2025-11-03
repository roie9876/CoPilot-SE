"""
Knowledge Graph Orchestrator

Core orchestration logic for the adaptive requirements gathering system.
Iteratively calls domain agents until all critical information is collected.
"""

import os
from typing import List, Optional, Tuple, Dict, Any
from pydantic import ValidationError

from src.models.knowledge_graph import (
    KnowledgeGraph,
    Context,
    Intent,
    Conflict,
    Status,
    IdentityAccess,
    RuntimePlatform,
    NetworkingConnectivity,
    DataPersistence,
    ResiliencyDR,
    SecurityGovernance,
    ExistingEnvironment,
)
from src.agents.domain_agents import (
    BaseDomainAgent,
    DomainAgentQuestion,
    IdentityDomainAgent,
    RuntimeDomainAgent,
    ResiliencyDomainAgent,
    NetworkingDomainAgent,
    DataDomainAgent,
)
from src.orchestrator.intent_extractor import IntentExtractor


class KnowledgeGraphOrchestrator:
    """
    Orchestrates the adaptive requirements gathering process.
    
    Workflow:
    1. Extract intent and context from user input
    2. Initialize knowledge graph with initial facts
    3. Iteratively select and run domain agents until ready_for_design = True
    4. Detect and resolve conflicts
    5. Return complete knowledge graph
    """

    def __init__(self):
        """Initialize the orchestrator with all domain agents."""
        self.intent_extractor = IntentExtractor()
        
        # Initialize all domain agents
        self.domain_agents: Dict[str, BaseDomainAgent] = {
            "identity_access": IdentityDomainAgent(),
            "runtime_platform": RuntimeDomainAgent(),
            "resiliency_dr": ResiliencyDomainAgent(),
            "networking_connectivity": NetworkingDomainAgent(),
            "data_persistence": DataDomainAgent(),
        }
        
        # Domain execution order based on intent
        self.domain_order_by_intent = {
            Intent.NEW_DEPLOYMENT: [
                "identity_access",
                "runtime_platform",
                "networking_connectivity",
                "data_persistence",
                "resiliency_dr",
            ],
            Intent.EXTEND_EXISTING: [
                "identity_access",
                "runtime_platform",
                "data_persistence",
                "networking_connectivity",
                "resiliency_dr",
            ],
            Intent.DR_ONLY: [
                "resiliency_dr",
                "data_persistence",
                "networking_connectivity",
                "identity_access",
                "runtime_platform",
            ],
            Intent.MIGRATION: [
                "runtime_platform",
                "data_persistence",
                "identity_access",
                "networking_connectivity",
                "resiliency_dr",
            ],
            Intent.OPTIMIZE_SECURITY: [
                "identity_access",
                "networking_connectivity",
                "data_persistence",
                "runtime_platform",
                "resiliency_dr",
            ],
            Intent.OPTIMIZE_COST: [
                "runtime_platform",
                "data_persistence",
                "resiliency_dr",
                "networking_connectivity",
                "identity_access",
            ],
        }

    def orchestrate(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> KnowledgeGraph:
        """
        Main orchestration method - runs the complete adaptive requirements gathering.
        
        Args:
            user_input: Natural language input from user
            conversation_history: Optional previous Q&A history
            
        Returns:
            Complete KnowledgeGraph ready for architecture design
            
        Raises:
            ValueError: If user input is invalid
            RuntimeError: If orchestration fails after max iterations
        """
        # Step 1: Extract intent and context
        print("\n[Orchestrator] Extracting intent and context...")
        context = self.intent_extractor.extract(user_input)
        print(f"[Orchestrator] Detected: {context.intent.value} for {context.cloud_provider.value}")
        print(f"[Orchestrator] Workload type: {context.workload_type.value}")
        
        # Step 2: Extract initial facts to pre-populate knowledge graph
        print("\n[Orchestrator] Extracting initial facts from user input...")
        initial_facts = self.intent_extractor.extract_initial_facts(user_input, context)
        
        # Step 3: Initialize knowledge graph
        kg = self._initialize_knowledge_graph(context, initial_facts)
        print(f"[Orchestrator] Knowledge graph initialized with {len(initial_facts)} domain(s) pre-populated")
        
        # Step 4: Iterative domain agent execution
        max_iterations = 20  # Safety limit
        iteration = 0
        
        while not kg.status.ready_for_design and iteration < max_iterations:
            iteration += 1
            print(f"\n[Orchestrator] === Iteration {iteration} ===")
            
            # Select next domain to process
            next_domain = self._select_next_domain(kg)
            if not next_domain:
                print("[Orchestrator] No more domains to process - computing readiness...")
                break
            
            print(f"[Orchestrator] Processing domain: {next_domain}")
            
            # Run the domain agent
            agent = self.domain_agents[next_domain]
            missing_fields = agent.get_missing_critical_fields(kg)
            questions = agent.generate_questions(missing_fields, kg)
            
            if not questions:
                print(f"[Orchestrator] No questions for {next_domain} - skipping")
                continue
            
            # In a real system, this would send questions to frontend and wait for answers
            # For now, we'll mark that this domain has been processed
            print(f"[Orchestrator] Generated {len(questions)} questions for {next_domain}")
            for q in questions:
                critical = "CRITICAL" if q.get("critical", False) else "optional"
                print(f"  - [{critical}] {q['question']}")
            
            # CRITICAL: In production, this is where you'd:
            # 1. Return questions to frontend
            # 2. Wait for user answers
            # 3. Update knowledge graph with answers
            # 4. Call agent.detect_conflicts(kg)
            # 5. Update confidence with agent.update_confidence(kg)
            
            # For this POC, we'll break here and let the API handle the interactive loop
            break
        
        # Step 5: Final conflict detection across all domains
        print("\n[Orchestrator] Running final conflict detection...")
        all_conflicts = self._detect_all_conflicts(kg)
        kg.status.conflicts = all_conflicts
        
        # Step 6: Compute final readiness
        kg.status.ready_for_design = self._compute_readiness(kg)
        
        print(f"\n[Orchestrator] Orchestration complete!")
        print(f"  - Critical gaps: {len(kg.status.critical_gaps)}")
        print(f"  - Conflicts: {len(kg.status.conflicts)}")
        print(f"  - Ready for design: {kg.status.ready_for_design}")
        
        return kg

    def process_user_answers(
        self,
        kg: KnowledgeGraph,
        domain: str,
        answers: Dict[str, Any],
    ) -> KnowledgeGraph:
        """
        Process user answers for a specific domain and update knowledge graph.
        
        This is called by the API after user answers questions.
        
        Args:
            kg: Current knowledge graph
            domain: Domain being updated (e.g., "identity_access")
            answers: Dictionary of field_name -> answer
            
        Returns:
            Updated knowledge graph
        """
        print(f"\n[Orchestrator] Processing answers for {domain}...")
        
        # Update the knowledge graph with answers
        domain_obj = getattr(kg, domain)
        for field_name, answer in answers.items():
            if hasattr(domain_obj, field_name):
                # Parse special fields that need transformation
                parsed_answer = self._parse_answer(field_name, answer)
                setattr(domain_obj, field_name, parsed_answer)
                if parsed_answer != answer:
                    print(f"  - Updated {field_name} = {answer} → {parsed_answer}")
                else:
                    print(f"  - Updated {field_name} = {answer}")
        
        # Update confidence for this domain
        agent = self.domain_agents[domain]
        new_confidence = agent.update_confidence(kg)
        domain_obj.confidence = new_confidence
        print(f"  - Confidence updated to {new_confidence:.2f}")
        
        # Detect conflicts for this domain
        conflicts = agent.detect_conflicts(kg)
        if conflicts:
            print(f"  - Detected {len(conflicts)} conflict(s)")
            kg.status.conflicts.extend(conflicts)
        
        # Update critical gaps
        kg.status.critical_gaps = self._compute_critical_gaps(kg)
        
        # Update readiness
        kg.status.ready_for_design = self._compute_readiness(kg)
        
        return kg

    def _parse_answer(self, field_name: str, answer: Any) -> Any:
        """
        Parse answer values that need transformation before storing in KG.
        
        Examples:
        - rto_minutes: "< 5 minutes ..." → 5 (int)
        - rpo_minutes: "Zero (no data loss)" → 0 (int)
        - multi_region: "Critical - Cannot afford..." → True (bool)
        """
        if not isinstance(answer, str):
            return answer
        
        # Parse RTO minutes from option text
        if field_name == "rto_minutes":
            if "< 5" in answer or "5 minutes" in answer:
                return 5
            elif "5-15" in answer or "15 minutes" in answer:
                return 15
            elif "15-60" in answer or "60 minutes" in answer:
                return 60
            elif "1-4 hours" in answer:
                return 240  # 4 hours
            elif "> 4 hours" in answer:
                return 480  # 8 hours
            return answer  # Fallback to original
        
        # Parse RPO minutes from option text
        if field_name == "rpo_minutes":
            if "Zero" in answer or "no data loss" in answer:
                return 0
            elif "< 5" in answer:
                return 5
            elif "5-15" in answer:
                return 15
            elif "15-60" in answer:
                return 60
            elif "> 1 hour" in answer:
                return 120  # 2 hours
            return answer  # Fallback to original
        
        # Parse multi_region boolean from business impact description
        if field_name == "multi_region":
            if "Critical" in answer or "High" in answer:
                return True
            elif "Medium" in answer or "Low" in answer:
                return False
            return answer  # Fallback to original
        
        # Parse ha_model from option text
        if field_name == "ha_model":
            if "Active-Active" in answer:
                return "active_active"
            elif "Active-Passive" in answer:
                return "active_passive"
            elif "Single Region" in answer:
                return "single_region"
            return answer  # Fallback to original
        
        # Parse regions_in_scope - convert string to list if needed
        if field_name == "regions_in_scope":
            if isinstance(answer, str):
                # Single region selected - convert to list
                return [answer]
            return answer  # Already a list
        
        return answer
    
    def _initialize_knowledge_graph(
        self,
        context: Context,
        initial_facts: Dict[str, Any],
    ) -> KnowledgeGraph:
        """Initialize knowledge graph with context and initial facts."""
        # Create empty domain objects
        identity_access = IdentityAccess()
        runtime_platform = RuntimePlatform()
        networking_connectivity = NetworkingConnectivity()
        data_persistence = DataPersistence()
        resiliency_dr = ResiliencyDR()
        security_governance = SecurityGovernance()
        existing_environment = ExistingEnvironment()
        
        # Pre-populate from initial facts
        if "identity_access" in initial_facts:
            for key, value in initial_facts["identity_access"].items():
                if hasattr(identity_access, key):
                    setattr(identity_access, key, value)
        
        if "runtime_platform" in initial_facts:
            for key, value in initial_facts["runtime_platform"].items():
                if hasattr(runtime_platform, key):
                    setattr(runtime_platform, key, value)
        
        if "networking_connectivity" in initial_facts:
            for key, value in initial_facts["networking_connectivity"].items():
                if hasattr(networking_connectivity, key):
                    setattr(networking_connectivity, key, value)
        
        if "data_persistence" in initial_facts:
            for key, value in initial_facts["data_persistence"].items():
                if hasattr(data_persistence, key):
                    setattr(data_persistence, key, value)
        
        if "resiliency_dr" in initial_facts:
            for key, value in initial_facts["resiliency_dr"].items():
                if hasattr(resiliency_dr, key):
                    setattr(resiliency_dr, key, value)
        
        if "security_governance" in initial_facts:
            for key, value in initial_facts["security_governance"].items():
                if hasattr(security_governance, key):
                    setattr(security_governance, key, value)
        
        # Create knowledge graph
        kg = KnowledgeGraph(
            context=context,
            existing_environment=existing_environment,
            identity_access=identity_access,
            runtime_platform=runtime_platform,
            networking_connectivity=networking_connectivity,
            data_persistence=data_persistence,
            resiliency_dr=resiliency_dr,
            security_governance=security_governance,
            status=Status(
                critical_gaps=[],
                conflicts=[],
                ready_for_design=False,
            ),
        )
        
        # Compute initial confidence for each domain
        for domain_name, agent in self.domain_agents.items():
            confidence = agent.update_confidence(kg)
            domain_obj = getattr(kg, domain_name)
            domain_obj.confidence = confidence
        
        # Compute initial critical gaps
        kg.status.critical_gaps = self._compute_critical_gaps(kg)
        
        return kg

    def _select_next_domain(self, kg: KnowledgeGraph) -> Optional[str]:
        """
        Select the next domain to process based on intent and current state.
        
        Priority:
        1. Domains with critical gaps (following intent-specific order)
        2. Domains with conflicts (need resolution)
        3. Domains with low confidence (following intent-specific order)
        
        Note: Critical gaps take priority over conflicts because we need complete
        information before we can properly resolve conflicts.
        
        Returns:
            Domain name (e.g., "identity_access") or None if all complete
        """
        # Get domain order for this intent
        domain_order = self.domain_order_by_intent.get(
            kg.context.intent,
            self.domain_order_by_intent[Intent.NEW_DEPLOYMENT],  # Default
        )
        
        # PRIORITY 1: Check for domains with critical gaps (CHANGED ORDER)
        for domain in domain_order:
            agent = self.domain_agents[domain]
            if not agent.is_relevant_for_intent(kg):
                print(f"[SelectDomain] Skipping {domain} - not relevant for intent")
                continue
            
            missing_fields = agent.get_missing_critical_fields(kg)
            if missing_fields:
                print(f"[SelectDomain] Selected {domain} - has {len(missing_fields)} critical gaps: {missing_fields}")
                return domain
            else:
                print(f"[SelectDomain] {domain} has no critical gaps")
        
        # PRIORITY 2: Check for domains with conflicts (MOVED TO SECOND)
        domains_with_conflicts = set()
        for conflict in kg.status.conflicts:
            domains_with_conflicts.update(conflict.domains_involved)
        
        for domain in domain_order:
            if domain in domains_with_conflicts:
                agent = self.domain_agents[domain]
                if agent.is_relevant_for_intent(kg):
                    print(f"[SelectDomain] Selected {domain} - has unresolved conflicts")
                    return domain
        
        # PRIORITY 3: Check for domains with low confidence (< 80%)
        for domain in domain_order:
            agent = self.domain_agents[domain]
            if not agent.is_relevant_for_intent(kg):
                continue
            
            domain_obj = getattr(kg, domain)
            if domain_obj.confidence < 0.8:
                return domain
        
        return None

    def _detect_all_conflicts(self, kg: KnowledgeGraph) -> List[Conflict]:
        """Run conflict detection across all domain agents."""
        all_conflicts = []
        
        for domain_name, agent in self.domain_agents.items():
            if not agent.is_relevant_for_intent(kg):
                continue
            
            conflicts = agent.detect_conflicts(kg)
            all_conflicts.extend(conflicts)
        
        return all_conflicts

    def _compute_critical_gaps(self, kg: KnowledgeGraph) -> List[str]:
        """Compute list of all critical fields that are still missing."""
        critical_gaps = []
        
        for domain_name, agent in self.domain_agents.items():
            if not agent.is_relevant_for_intent(kg):
                continue
            
            missing_fields = agent.get_missing_critical_fields(kg)
            for field in missing_fields:
                critical_gaps.append(f"{domain_name}.{field}")
        
        return critical_gaps

    def _compute_readiness(self, kg: KnowledgeGraph) -> bool:
        """
        Determine if knowledge graph is ready for architecture design.
        
        Criteria:
        1. No critical gaps remaining
        2. No unresolved HIGH severity conflicts
        3. All relevant domains have confidence >= 80%
        
        Returns:
            True if ready for design, False otherwise
        """
        # Check for critical gaps
        if kg.status.critical_gaps:
            print(f"[Readiness] Not ready - {len(kg.status.critical_gaps)} critical gaps remain")
            return False
        
        # Check for CRITICAL-severity unresolved conflicts only
        # (High-severity conflicts are warnings and don't block design)
        critical_conflicts = [c for c in kg.status.conflicts if c.severity == "critical"]
        if critical_conflicts:
            print(f"[Readiness] Not ready - {len(critical_conflicts)} critical-severity conflicts unresolved")
            return False
        
        # Check confidence for all relevant domains
        for domain_name, agent in self.domain_agents.items():
            if not agent.is_relevant_for_intent(kg):
                continue
            
            domain_obj = getattr(kg, domain_name)
            if domain_obj.confidence < 0.8:
                print(f"[Readiness] Not ready - {domain_name} confidence only {domain_obj.confidence:.2f}")
                return False
        
        print("[Readiness] ✅ Ready for architecture design!")
        return True

    def get_next_questions(self, kg: KnowledgeGraph) -> Tuple[str, List[DomainAgentQuestion]]:
        """
        Get the next set of questions to ask the user.
        
        Returns:
            Tuple of (domain_name, questions)
        """
        print(f"\n[GetNextQuestions] Current critical gaps: {len(kg.status.critical_gaps)}")
        next_domain = self._select_next_domain(kg)
        if not next_domain:
            print("[GetNextQuestions] No next domain selected - all done!")
            return ("", [])
        
        print(f"[GetNextQuestions] Selected domain: {next_domain}")
        agent = self.domain_agents[next_domain]
        missing_fields = agent.get_missing_critical_fields(kg)
        questions = agent.generate_questions(missing_fields, kg)
        
        return (next_domain, questions)
