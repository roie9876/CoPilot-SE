"""
Requirements Agent - Extracts structured requirements from natural language.

This agent:
1. Parses user input to extract requirements
2. Detects target cloud platform (Azure/AWS/GCP/Oracle)
3. Identifies industry vertical
4. Extracts functional/non-functional requirements
5. Detects ambiguities and asks clarifying questions
"""

from typing import Dict, List, Optional
import re
import logging

from src.agents.base_agent import BaseAgent
from src.models.schemas import (
    RequirementsInput,
    RequirementsOutput,
    NonFunctionalRequirements,
    TechnicalConstraints,
    CloudPlatform,
    IndustryVertical,
    ErrorType,
    normalize_cloud_platform,
)

logger = logging.getLogger(__name__)


class RequirementsAgent(BaseAgent):
    """
    Requirements extraction agent.
    
    Uses chain-of-thought reasoning to:
    - Understand user intent
    - Extract requirements
    - Detect target cloud platform
    - Identify ambiguities
    """
    
    # Cloud service keywords for detection
    CLOUD_KEYWORDS = {
        CloudPlatform.AZURE: [
            # Compute
            'app service', 'azure functions', 'aks', 'azure kubernetes',
            'virtual machines', 'vm', 'container instances', 'aci',
            'container apps', 'aca', 'batch', 'service fabric',
            # Storage
            'blob storage', 'table storage', 'queue storage', 'file storage',
            'azure storage', 'data lake',
            # Database
            'cosmos db', 'sql database', 'azure sql', 'postgresql flexible',
            'mysql flexible', 'synapse', 'sql managed instance',
            # Networking
            'application gateway', 'front door', 'traffic manager',
            'load balancer', 'vnet', 'virtual network',
            # Azure-specific
            'azure', 'microsoft azure', 'entra', 'active directory'
        ],
        CloudPlatform.AWS: [
            # Compute
            'ec2', 'lambda', 'elastic beanstalk', 'ecs', 'eks', 'fargate',
            'lightsail', 'batch',
            # Storage
            's3', 'ebs', 'efs', 'fsx', 'storage gateway',
            # Database
            'rds', 'dynamodb', 'aurora', 'redshift', 'neptune', 'elasticache',
            # Networking
            'elb', 'alb', 'nlb', 'cloudfront', 'route 53', 'api gateway',
            # AWS-specific
            'aws', 'amazon web services'
        ],
        CloudPlatform.GCP: [
            # Compute
            'compute engine', 'cloud functions', 'gke', 'cloud run',
            'app engine', 'cloud functions',
            # Storage
            'cloud storage', 'persistent disk', 'filestore',
            # Database
            'cloud sql', 'firestore', 'bigtable', 'spanner', 'memorystore',
            # Networking
            'cloud load balancing', 'cloud cdn', 'cloud dns',
            # GCP-specific
            'gcp', 'google cloud', 'google cloud platform'
        ],
        CloudPlatform.ORACLE: [
            # Compute
            'oke', 'oracle kubernetes', 'compute instances',
            # Database
            'autonomous database', 'oracle database', 'nosql database',
            # Oracle-specific
            'oracle cloud', 'oci', 'oracle'
        ]
    }
    
    # Industry vertical keywords
    INDUSTRY_KEYWORDS = {
        IndustryVertical.HEALTHCARE: [
            'healthcare', 'health', 'hipaa', 'patient', 'medical', 'hospital',
            'clinical', 'ehr', 'emr', 'phi', 'health records'
        ],
        IndustryVertical.FINANCE: [
            'finance', 'financial', 'banking', 'payment', 'pci dss', 'pci',
            'trading', 'fintech', 'transaction', 'sox', 'pcidss'
        ],
        IndustryVertical.PUBLIC_SECTOR: [
            'government', 'public sector', 'federal', 'state', 'municipal',
            'fedramp', 'fisma', 'public'
        ],
        IndustryVertical.RETAIL: [
            'retail', 'e-commerce', 'ecommerce', 'shopping', 'store',
            'marketplace', 'cart', 'checkout', 'product catalog'
        ],
        IndustryVertical.MANUFACTURING: [
            'manufacturing', 'factory', 'industrial', 'iot', 'sensors',
            'production', 'supply chain', 'inventory'
        ]
    }
    
    def __init__(self):
        """Initialize Requirements Agent."""
        super().__init__(name="RequirementsAgent")
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Extract requirements from user input.
        
        Args:
            input_data: Dict with 'user_input' and optional 'context'
            
        Returns:
            RequirementsOutput dict
        """
        self._record_invocation()
        
        try:
            # Validate input
            req_input = RequirementsInput(**input_data)
            
            self.logger.info(f"Processing input: {req_input.user_input[:100]}...")
            
            # Extract requirements using pattern matching and keyword detection
            output = RequirementsOutput()
            
            # 1. Detect cloud platform
            output.target_cloud = self._detect_cloud_platform(req_input.user_input)
            
            # 2. Detect industry vertical
            output.industry_vertical = self._detect_industry(req_input.user_input)
            
            # 3. Extract functional requirements
            output.functional_requirements = self._extract_functional_requirements(
                req_input.user_input
            )
            
            # 4. Extract non-functional requirements
            output.non_functional_requirements = self._extract_non_functional_requirements(
                req_input.user_input
            )
            
            # 5. Extract technical constraints
            output.technical_constraints = self._extract_constraints(
                req_input.user_input
            )
            
            # 6. Detect implied requirements
            output.implied_requirements = self._detect_implied_requirements(
                output, req_input.user_input
            )
            
            # 7. Check for ambiguities
            output = self._check_ambiguities(output, req_input.user_input)
            
            # 8. Calculate confidence score
            output.confidence_score = self._calculate_confidence(output)
            
            self.logger.info(
                f"Extracted requirements: cloud={output.target_cloud}, "
                f"functional={len(output.functional_requirements)}, "
                f"needs_clarification={output.needs_clarification}"
            )
            
            return output
        
        except Exception as e:
            self.logger.error(f"Error processing requirements: {e}", exc_info=True)
            error = self._create_error(
                f"Failed to extract requirements: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                retryable=True
            )
            raise error
    
    def _detect_cloud_platform(self, user_input: str) -> Optional[CloudPlatform]:
        """
        Detect target cloud platform from user input.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Detected CloudPlatform or None
        """
        input_lower = user_input.lower()
        
        # Check for explicit mentions
        for cloud, keywords in self.CLOUD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in input_lower:
                    self.logger.info(f"Detected {cloud} from keyword: {keyword}")
                    return cloud
        
        # If no cloud detected, check for generic cloud terms
        if any(term in input_lower for term in ['cloud', 'deploy', 'host', 'infrastructure']):
            self.logger.info("Generic cloud terms found but no specific platform detected")
            return None  # Will trigger clarification
        
        return None
    
    def _detect_industry(self, user_input: str) -> IndustryVertical:
        """
        Detect industry vertical from user input.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            Detected IndustryVertical (default: GENERAL)
        """
        input_lower = user_input.lower()
        
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in input_lower:
                    self.logger.info(f"Detected industry: {industry}")
                    return industry
        
        return IndustryVertical.GENERAL
    
    def _extract_functional_requirements(self, user_input: str) -> List[str]:
        """
        Extract functional requirements (what the system must do).
        
        Args:
            user_input: User's natural language request
            
        Returns:
            List of functional requirements
        """
        requirements = []
        input_lower = user_input.lower()
        
        # Pattern: action verbs
        action_patterns = [
            (r'need to ([\w\s]+)', 'System must {}'),
            (r'should ([\w\s]+)', 'System should {}'),
            (r'must ([\w\s]+)', 'System must {}'),
            (r'want to ([\w\s]+)', 'System should {}'),
            (r'require ([\w\s]+)', 'System requires {}'),
        ]
        
        for pattern, template in action_patterns:
            matches = re.findall(pattern, input_lower)
            for match in matches:
                requirements.append(template.format(match.strip()))
        
        # Common functional requirements by keyword
        if 'e-commerce' in input_lower or 'shopping' in input_lower:
            requirements.extend([
                "Product catalog management",
                "Shopping cart functionality",
                "Payment processing",
                "Order management"
            ])
        
        if 'api' in input_lower:
            requirements.append("RESTful API endpoints")
        
        if 'database' in input_lower:
            requirements.append("Data persistence layer")
        
        if 'authentication' in input_lower or 'login' in input_lower:
            requirements.append("User authentication and authorization")
        
        return list(set(requirements))  # Remove duplicates
    
    def _extract_non_functional_requirements(
        self, user_input: str
    ) -> NonFunctionalRequirements:
        """
        Extract non-functional requirements.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            NonFunctionalRequirements instance
        """
        nfr = NonFunctionalRequirements()
        input_lower = user_input.lower()
        
        # Scalability
        user_match = re.search(r'(\d+[,\d]*)\s*(?:concurrent\s+)?users?', input_lower)
        if user_match:
            user_count = int(user_match.group(1).replace(',', ''))
            nfr.scalability = {
                "target_users": user_count,
                "concurrent_users": user_count // 10  # Assume 10% concurrent
            }
        
        # Performance
        if 'latency' in input_lower or 'response time' in input_lower:
            nfr.performance["latency_requirement"] = "low"
        
        if 'real-time' in input_lower or 'realtime' in input_lower:
            nfr.performance["real_time"] = True
        
        # Availability
        if 'high availability' in input_lower or 'ha' in input_lower:
            nfr.availability = {"target_uptime": "99.9%", "multi_az": True}
        
        if '24/7' in input_lower or '24x7' in input_lower:
            nfr.availability["continuous_operation"] = True
        
        # Security
        if any(term in input_lower for term in ['secure', 'security', 'encrypted', 'encryption']):
            nfr.security = {"encryption_required": True}
        
        # Compliance
        compliance_keywords = {
            'hipaa': 'HIPAA',
            'pci': 'PCI DSS',
            'pci dss': 'PCI DSS',
            'pcidss': 'PCI DSS',
            'gdpr': 'GDPR',
            'sox': 'SOX',
            'fedramp': 'FedRAMP',
            'fisma': 'FISMA'
        }
        
        for keyword, standard in compliance_keywords.items():
            if keyword in input_lower:
                nfr.compliance.append(standard)
        
        return nfr
    
    def _extract_constraints(self, user_input: str) -> TechnicalConstraints:
        """
        Extract technical constraints.
        
        Args:
            user_input: User's natural language request
            
        Returns:
            TechnicalConstraints instance
        """
        constraints = TechnicalConstraints()
        input_lower = user_input.lower()
        
        # Budget
        budget_patterns = [
            r'\$(\d+[,\d]*)\s*(?:per\s+)?(?:month|monthly)',
            r'budget\s+of\s+\$(\d+[,\d]*)',
            r'(\d+[,\d]*)\s+dollars?\s+(?:per\s+)?month'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, input_lower)
            if match:
                amount = int(match.group(1).replace(',', ''))
                constraints.budget = {"monthly": amount, "currency": "USD"}
                break
        
        # Team skills
        tech_keywords = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'java': 'Java',
            'c#': 'C#',
            'react': 'React',
            'angular': 'Angular',
            'vue': 'Vue.js',
            'node': 'Node.js',
            'nodejs': 'Node.js',
            '.net': '.NET',
            'dotnet': '.NET'
        }
        
        for keyword, tech in tech_keywords.items():
            if keyword in input_lower:
                constraints.team_skills.append(tech)
        
        # Timeline
        timeline_patterns = [
            r'(\d+)\s+weeks?',
            r'(\d+)\s+months?',
            r'by\s+(\w+\s+\d+)'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, input_lower)
            if match:
                constraints.timeline = match.group(0)
                break
        
        return constraints
    
    def _detect_implied_requirements(
        self, output: RequirementsOutput, user_input: str
    ) -> List[str]:
        """
        Detect implied requirements based on extracted data.
        
        Args:
            output: Current requirements output
            user_input: Original user input
            
        Returns:
            List of implied requirements
        """
        implied = []
        
        # If compliance is required, imply security
        if output.non_functional_requirements.compliance:
            implied.append("Enhanced security controls for compliance")
            implied.append("Audit logging and monitoring")
        
        # If high user count, imply scalability
        scalability = output.non_functional_requirements.scalability
        if scalability and scalability.get("target_users", 0) > 5000:
            implied.append("Auto-scaling capabilities")
            implied.append("Load balancing")
        
        # If e-commerce, imply payment and inventory
        if output.industry_vertical == IndustryVertical.RETAIL:
            implied.append("Secure payment gateway integration")
            implied.append("Inventory management system")
        
        # If healthcare, imply data encryption
        if output.industry_vertical == IndustryVertical.HEALTHCARE:
            implied.append("Data encryption at rest and in transit")
            implied.append("Access control and audit trails")
        
        return implied
    
    def _check_ambiguities(
        self, output: RequirementsOutput, user_input: str
    ) -> RequirementsOutput:
        """
        Check for ambiguities and generate clarifying questions.
        
        Args:
            output: Current requirements output
            user_input: Original user input
            
        Returns:
            Updated RequirementsOutput with clarifying questions if needed
        """
        ambiguities = []
        questions = []
        
        # Check if cloud platform is missing
        if output.target_cloud is None:
            ambiguities.append("Target cloud platform not specified")
            questions.append(
                "Which cloud platform would you like to use? "
                "(AWS, Azure, Google Cloud, Oracle Cloud)"
            )
        
        # Check if user count is missing
        if not output.non_functional_requirements.scalability:
            ambiguities.append("Expected user count not specified")
            questions.append("How many users do you expect? (concurrent and total)")
        
        # Check if budget is missing
        if not output.technical_constraints.budget:
            ambiguities.append("Budget not specified")
            questions.append("What is your monthly budget for this solution?")
        
        # Check if functional requirements are vague
        if len(output.functional_requirements) < 2:
            ambiguities.append("Few functional requirements detected")
            questions.append(
                "Can you provide more details about what the system should do? "
                "(e.g., specific features, workflows, integrations)"
            )
        
        # Set clarification needed if there are critical ambiguities
        if output.target_cloud is None or len(output.functional_requirements) < 2:
            output.needs_clarification = True
            output.clarifying_questions = questions
            output.ambiguities_detected = ambiguities
        
        return output
    
    def _calculate_confidence(self, output: RequirementsOutput) -> float:
        """
        Calculate confidence score for extracted requirements.
        
        Args:
            output: Requirements output
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0
        
        # Cloud platform detected (+0.3)
        if output.target_cloud:
            score += 0.3
        
        # Functional requirements (+0.2)
        if len(output.functional_requirements) >= 3:
            score += 0.2
        elif len(output.functional_requirements) > 0:
            score += 0.1
        
        # Non-functional requirements (+0.2)
        if output.non_functional_requirements.scalability:
            score += 0.1
        if output.non_functional_requirements.compliance:
            score += 0.1
        
        # Technical constraints (+0.2)
        if output.technical_constraints.budget:
            score += 0.1
        if output.technical_constraints.team_skills:
            score += 0.1
        
        # No clarification needed (+0.1)
        if not output.needs_clarification:
            score += 0.1
        
        return min(score, 1.0)
