import React, { useState } from 'react';
import { Sparkles, ArrowLeft, CheckCircle2 } from 'lucide-react';
import DomainProgressBar from './DomainProgressBar';
import AdaptiveQuestionForm from './AdaptiveQuestionForm';
import ConflictResolutionPanel from './ConflictResolutionPanel';
import ReadinessIndicator from './ReadinessIndicator';
import ArchitectureView from './ArchitectureView';
import type {
  KGStartResponse,
  KGAnswerResponse,
  KGArchitectureResponse,
  Conflict,
  ServiceCost,
  CostOutput as KGCostOutput,
  DocumentationOutput as KGDocumentationOutput,
} from '../types-kg';
import type { ArchitectureOutput, CostOutput, DocumentationOutput } from '../types';
import { kgStart, kgAnswer, kgArchitecture, kgValidate } from '../api/kg-client';

type WizardState =
  | 'initial'
  | 'validating'
  | 'gathering'
  | 'ready'
  | 'generating'
  | 'complete'
  | 'error';

interface KGWizardProps {
  initialRequirements?: string;
  onBack?: () => void;
}

const KGWizard: React.FC<KGWizardProps> = ({ initialRequirements, onBack }) => {
  // Wizard state
  const [state, setState] = useState<WizardState>('initial');
  const [error, setError] = useState<string | null>(null);

  // Session data
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [requirements, setRequirements] = useState(initialRequirements || '');

  // Knowledge Graph state
  const [currentDomain, setCurrentDomain] = useState<string | null>(null);
  const [questions, setQuestions] = useState<KGStartResponse['questions']>([]);
  const [domainConfidence, setDomainConfidence] = useState<KGStartResponse['domain_confidence']>({
    identity: 0,
    runtime: 0,
    networking: 0,
    data: 0,
    resiliency: 0,
    security: 0,
    monitoring: 0,
  });
  const [readyForDesign, setReadyForDesign] = useState(false);
  const [criticalGaps, setCriticalGaps] = useState(0);
  const [conflictsCount, setConflictsCount] = useState(0);
  const [conflictsDetail, setConflictsDetail] = useState<Conflict[]>([]);
  const [overallConfidence, setOverallConfidence] = useState(0);

  // Architecture result
  const [architecture, setArchitecture] = useState<ArchitectureOutput | null>(null);
  const [costEstimate, setCostEstimate] = useState<KGCostOutput | null>(null);
  const [documentation, setDocumentation] = useState<KGDocumentationOutput | null>(null);

  // Submitting state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Expanded service details
  const [expandedServiceIndex, setExpandedServiceIndex] = useState<number | null>(null);

  // Start Knowledge Graph session
  const handleStartSession = async () => {
    if (!requirements.trim()) {
      setError('Please enter your requirements');
      return;
    }

    setState('validating');
    setError(null);
    setIsSubmitting(true);

    try {
      // STEP 1: Pre-validate the request
      console.log('🔍 Validating request...');
      const validationResult = await kgValidate(requirements);
      
      console.log('Validation result:', validationResult);
      
      // Check if request is valid
      if (!validationResult.is_valid) {
        setError(
          `❌ ${validationResult.reason}\n\n💡 ${validationResult.suggestion}`
        );
        setState('error');
        setIsSubmitting(false);
        return;
      }
      
      // If confidence is low, warn user but proceed
      if (validationResult.confidence < 0.7) {
        console.warn('⚠️ Low validation confidence:', validationResult.confidence);
      }

      // STEP 2: Start requirements gathering
      console.log('✅ Request validated, starting KG session...');
      setState('gathering');
      
      const response = await kgStart(requirements);
      setSessionId(response.session_id);
      setCurrentDomain(response.domain);
      setQuestions(response.questions);
      setDomainConfidence(response.domain_confidence);
      setReadyForDesign(response.ready_for_design);
      setCriticalGaps(response.critical_gaps);
      setConflictsCount(response.conflicts);
      setOverallConfidence(response.overall_confidence);

      if (response.ready_for_design) {
        setState('ready');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session');
      setState('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit answers for current domain
  const handleSubmitAnswers = async (
    answers: Record<string, string | number | boolean | string[]>
  ) => {
    if (!sessionId || !currentDomain) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response: KGAnswerResponse = await kgAnswer(sessionId, currentDomain, answers);
      setCurrentDomain(response.domain);
      setQuestions(response.questions);
      setDomainConfidence(response.domain_confidence);
      setReadyForDesign(response.ready_for_design);
      setCriticalGaps(response.critical_gaps);
      setConflictsCount(response.conflicts);
      setOverallConfidence(response.overall_confidence);

      if (response.ready_for_design) {
        setState('ready');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit answers');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Generate architecture from KG
  const handleGenerateArchitecture = async () => {
    if (!sessionId) return;

    setState('generating');
    setError(null);

    try {
      const response: KGArchitectureResponse = await kgArchitecture(sessionId);
      
      if (response.status === 'success' && response.architecture) {
        setArchitecture(response.architecture);
        setCostEstimate(response.cost_estimate || null);
        setDocumentation(response.documentation || null);
        setState('complete');
      } else {
        setError(response.error || 'Failed to generate architecture');
        setState('error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate architecture');
      setState('error');
    }
  };

  // Map KG API types to App types for ArchitectureView
  const mapKGCostToAppCost = (kgCost: KGCostOutput, arch: ArchitectureOutput): CostOutput => {
    return {
      target_cloud: arch.target_cloud,
      region: arch.region,
      currency: kgCost.currency,
      time_period: kgCost.time_period,
      service_costs: kgCost.service_costs.map(sc => ({
        ...sc,
        category: sc.category || 'Other',
        pricing_model: sc.pricing_model || 'Pay-as-you-go',
        pricing_tier: sc.pricing_tier || 'Standard',
        pricing_url: sc.pricing_url || '',
        assumptions: {},
        cost_breakdown: {},
      })),
      total_monthly_cost_low: kgCost.total_monthly_cost_low,
      total_monthly_cost_medium: kgCost.total_monthly_cost_medium,
      total_monthly_cost_high: kgCost.total_monthly_cost_high,
      cost_by_category: {},
      cost_optimization_recommendations: [],
      assumptions: kgCost.assumptions || [],
      disclaimers: ['Cost estimates are approximate and may vary based on actual usage.'],
      confidence_level: 'medium',
      sources: kgCost.citations?.map(c => ({
        title: c || 'Azure Pricing',
        url: '',
        relevance: 'pricing',
        accessed_at: new Date().toISOString(),
      })) || [],
      citations: kgCost.citations?.map(c => ({
        title: c || 'Azure Pricing',
        url: '',
        relevance: 'pricing',
        accessed_at: new Date().toISOString(),
      })) || [],
    };
  };

  const mapKGDocToAppDoc = (kgDoc: KGDocumentationOutput): DocumentationOutput => {
    return {
      format: kgDoc.format,
      content: kgDoc.content,
      diagrams: [],
      metadata: {
        title: 'Architecture Documentation',
        generated_at: new Date().toISOString(),
        cloud_platform: 'Azure',
        version: '1.0',
        filename: 'architecture.md',
        author: 'Co-Pilot SE',
      },
      export_formats: ['markdown', 'pdf'],
    };
  };

  // Reset wizard
  const handleReset = () => {
    setState('initial');
    setSessionId(null);
    setRequirements(initialRequirements || '');
    setCurrentDomain(null);
    setQuestions([]);
    setDomainConfidence({
      identity: 0,
      runtime: 0,
      networking: 0,
      data: 0,
      resiliency: 0,
      security: 0,
      monitoring: 0,
    });
    setReadyForDesign(false);
    setCriticalGaps(0);
    setConflictsCount(0);
    setConflictsDetail([]);
    setOverallConfidence(0);
    setArchitecture(null);
    setError(null);
  };

  // Render initial input form
  const renderInitialForm = () => (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex items-center space-x-3 mb-6">
          <Sparkles className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">
            Architecture Wizard
          </h1>
        </div>

        <p className="text-gray-600 mb-6">
          Describe your cloud architecture requirements in natural language. Our AI will guide you
          through a series of adaptive questions to gather all necessary information.
        </p>

        <div className="space-y-4">
          <div>
            <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-2">
              What cloud architecture do you need?
            </label>
            <textarea
              id="requirements"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Example: Design an Azure solution with specific requirements for identity (authentication), runtime (compute), networking (connectivity), data (storage), security (compliance), resiliency (availability), and monitoring (observability)..."
              disabled={isSubmitting}
            />
            <p className="mt-2 text-sm text-gray-500">
              Minimum 10 characters. Include requirements, constraints, and budget.
            </p>
          </div>

          {/* Example Scenarios */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-3">Or try an example:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <button
                onClick={() => setRequirements("Design a highly available Azure e-commerce platform for 50,000 concurrent users with PCI DSS compliance, Azure AD B2C authentication, CDN for global traffic, geo-replicated SQL databases, Azure Key Vault for secrets, 99.99% SLA, and Application Insights monitoring. Budget: $5,000/month")}
                className="text-left p-3 border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition text-sm text-blue-600"
                disabled={isSubmitting}
              >
                <span className="font-semibold block mb-1">🛒 E-Commerce Platform (High Availability)</span>
                <span className="text-xs text-gray-600">Covers: Identity (Azure AD B2C), Networking (CDN), Data (geo-replication), Security (Key Vault, PCI DSS), Resiliency (99.99% SLA), Monitoring (App Insights)</span>
              </button>
              <button
                onClick={() => setRequirements("Build a secure multi-tenant SaaS application on Azure with AKS microservices, Azure Private Link networking, Azure SQL with private endpoints, managed identity authentication, auto-scaling (10-100 pods), backup to geo-redundant storage, Azure Monitor alerts, and zero-downtime deployments. Expected: 10,000 users")}
                className="text-left p-3 border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition text-sm text-blue-600"
                disabled={isSubmitting}
              >
                <span className="font-semibold block mb-1">🏢 Multi-Tenant SaaS (AKS Microservices)</span>
                <span className="text-xs text-gray-600">Covers: Identity (managed identity), Runtime (AKS, auto-scaling), Networking (Private Link), Data (Azure SQL, backups), Security (private endpoints), Resiliency (zero-downtime), Monitoring (Azure Monitor)</span>
              </button>
              <button
                onClick={() => setRequirements("Create an Azure serverless IoT solution with Event Hubs for 1M device messages/day, Azure Functions for real-time processing, Time Series Insights for analytics, Cosmos DB with multi-region writes, DDoS protection, API Management with OAuth2, automatic failover, and Log Analytics dashboards")}
                className="text-left p-3 border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition text-sm text-blue-600"
                disabled={isSubmitting}
              >
                <span className="font-semibold block mb-1">📡 IoT Platform (Serverless & Real-Time)</span>
                <span className="text-xs text-gray-600">Covers: Identity (OAuth2), Runtime (Functions, Event Hubs), Networking (API Management), Data (Cosmos DB, multi-region), Security (DDoS protection), Resiliency (auto failover), Monitoring (Log Analytics)</span>
              </button>
              <button
                onClick={() => setRequirements("Design a HIPAA-compliant healthcare data platform on Azure with Azure Synapse Analytics, Data Lake Storage with encryption at rest, VNet service endpoints, Azure Firewall, role-based access control, automated backups with 7-year retention, compliance reports, and real-time alerting for security events")}
                className="text-left p-3 border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition text-sm text-blue-600"
                disabled={isSubmitting}
              >
                <span className="font-semibold block mb-1">🏥 Healthcare Data Platform (HIPAA Compliance)</span>
                <span className="text-xs text-gray-600">Covers: Identity (RBAC), Runtime (Synapse Analytics), Networking (VNet, Firewall), Data (Data Lake, encryption, 7-year backups), Security (HIPAA, compliance reports), Monitoring (real-time security alerts)</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-red-800">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end">
            {onBack && (
              <button
                onClick={onBack}
                className="px-6 py-3 text-gray-700 hover:text-gray-900 flex items-center space-x-2 mr-auto"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back</span>
              </button>
            )}
            <button
              onClick={handleStartSession}
              disabled={isSubmitting || !requirements.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2 font-medium shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Start Wizard</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render gathering state
  const renderGathering = () => (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              Requirements Gathering
            </h1>
            <p className="text-gray-600">
              Original request: <span className="font-medium">{requirements}</span>
            </p>
          </div>
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg"
          >
            Start Over
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <DomainProgressBar
        domainConfidence={domainConfidence}
        currentDomain={currentDomain}
        readyForDesign={readyForDesign}
      />

      {/* Conflicts */}
      {conflictsDetail.length > 0 && (
        <ConflictResolutionPanel conflicts={conflictsDetail} />
      )}

      {/* Readiness Indicator */}
      <ReadinessIndicator
        readyForDesign={readyForDesign}
        criticalGaps={criticalGaps}
        conflicts={conflictsCount}
        overallConfidence={overallConfidence}
      />

      {/* Questions Form */}
      {questions.length > 0 && currentDomain && sessionId && (
        <AdaptiveQuestionForm
          domain={currentDomain}
          questions={questions}
          onSubmit={handleSubmitAnswers}
          isSubmitting={isSubmitting}
          sessionId={sessionId}
        />
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-800">
          {error}
        </div>
      )}
    </div>
  );

  // Render ready state
  const renderReady = () => (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-8 h-8 text-green-500" />
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Ready to Generate Architecture
              </h1>
              <p className="text-gray-600">
                All requirements collected successfully!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Summary */}
      <DomainProgressBar
        domainConfidence={domainConfidence}
        currentDomain={null}
        readyForDesign={readyForDesign}
      />

      {/* Readiness Indicator */}
      <ReadinessIndicator
        readyForDesign={readyForDesign}
        criticalGaps={criticalGaps}
        conflicts={conflictsCount}
        overallConfidence={overallConfidence}
      />

      {/* Generate Button */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <p className="text-gray-700 mb-4">
            You can now generate your cloud architecture design based on the collected requirements.
          </p>
          <button
            onClick={handleGenerateArchitecture}
            className="px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 text-lg font-medium flex items-center space-x-2 mx-auto"
          >
            <Sparkles className="w-6 h-6" />
            <span>Generate Architecture</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Render generating state
  const renderGenerating = () => (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
        <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Generating Architecture...
        </h2>
        <p className="text-gray-600">
          Please wait while we design your cloud architecture based on your requirements.
        </p>
      </div>
    </div>
  );

  // Render complete state
  const renderComplete = () => (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-8 h-8 text-green-500" />
            <h1 className="text-2xl font-bold text-gray-800">
              Architecture Generated Successfully
            </h1>
          </div>
          <button
            onClick={handleReset}
            className="px-4 py-2 text-blue-600 hover:text-blue-800 border border-blue-300 rounded-lg"
          >
            Start New Design
          </button>
        </div>
      </div>

      {architecture && (
        <ArchitectureView 
          architecture={architecture} 
          costs={costEstimate ? mapKGCostToAppCost(costEstimate, architecture) : undefined}
          documentation={documentation ? mapKGDocToAppDoc(documentation) : undefined}
        />
      )}

      {/* Cost Estimate Section */}
      {costEstimate && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-800">💰 Cost Estimate</h2>
            <div className="text-sm text-gray-600">
              <span className="font-medium">Region:</span> {architecture?.region || 'Not specified'} | 
              <span className="font-medium ml-2">Cloud:</span> {architecture?.target_cloud || 'Azure'}
            </div>
          </div>
          
          {/* Total Cost Summary */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-600">Low Usage</div>
              <div className="text-2xl font-bold text-green-600">
                ${costEstimate.total_monthly_cost_low?.toFixed(2) || 'N/A'}/mo
              </div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600">Medium Usage</div>
              <div className="text-2xl font-bold text-blue-600">
                ${costEstimate.total_monthly_cost_medium?.toFixed(2) || 'N/A'}/mo
              </div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-gray-600">High Usage</div>
              <div className="text-2xl font-bold text-orange-600">
                ${costEstimate.total_monthly_cost_high?.toFixed(2) || 'N/A'}/mo
              </div>
            </div>
          </div>

          {/* Cost Breakdown by Service */}
          {costEstimate.service_costs && costEstimate.service_costs.length > 0 && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-semibold text-gray-800">Cost Breakdown by Service</h3>
                <span className="text-xs text-gray-500 italic">
                  💡 Click any row to see detailed breakdown
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Service
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU/Tier
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Monthly Cost
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        % of Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costEstimate.service_costs.map((service: ServiceCost, index: number) => {
                      const monthlyCost = service.medium_usage_monthly || 0;
                      const percentage = costEstimate.total_monthly_cost_medium 
                        ? ((monthlyCost / costEstimate.total_monthly_cost_medium) * 100).toFixed(1)
                        : '0';
                      const isExpanded = expandedServiceIndex === index;
                      
                      // Find matching architecture service to get detailed SKU info
                      const archService = architecture?.services.find(
                        s => s.service_name.toLowerCase().includes(service.service_name.toLowerCase()) ||
                             service.service_name.toLowerCase().includes(s.service_name.toLowerCase())
                      );
                      const detailedSKU = archService?.configuration?.sku || 
                                        archService?.configuration?.instance_type ||
                                        service.pricing_tier || 
                                        service.sku || 
                                        service.tier || 
                                        'Standard';
                      const replicas = archService?.configuration?.replicas;
                      
                      return (
                        <>
                          <tr 
                            key={index} 
                            className="hover:bg-gray-50 cursor-pointer transition-colors"
                            onClick={() => setExpandedServiceIndex(isExpanded ? null : index)}
                          >
                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                              <div className="flex items-center">
                                <span className="mr-2">
                                  {isExpanded ? '▼' : '▶'}
                                </span>
                                {service.service_name || 'Unknown Service'}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              <div className="flex flex-col">
                                <span>{detailedSKU}</span>
                                {replicas && replicas > 1 && (
                                  <span className="text-xs text-gray-400">×{replicas} replicas</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                              ${monthlyCost.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-sm text-right text-gray-500">
                              {percentage}%
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr key={`${index}-details`} className="bg-blue-50">
                              <td colSpan={4} className="px-4 py-4">
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <h4 className="font-semibold text-gray-900 mb-2">💰 Cost Breakdown</h4>
                                    <div className="space-y-1 text-gray-700">
                                      <div className="flex justify-between">
                                        <span>Low Usage:</span>
                                        <span className="font-medium text-green-600">
                                          ${service.low_usage_monthly?.toFixed(2) || '0.00'}/mo
                                        </span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span>Medium Usage:</span>
                                        <span className="font-medium text-blue-600">
                                          ${service.medium_usage_monthly?.toFixed(2) || '0.00'}/mo
                                        </span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span>High Usage:</span>
                                        <span className="font-medium text-orange-600">
                                          ${service.high_usage_monthly?.toFixed(2) || '0.00'}/mo
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                  <div>
                                    <h4 className="font-semibold text-gray-900 mb-2">📋 Service Details</h4>
                                    <div className="space-y-1 text-gray-700">
                                      <div><strong>Category:</strong> {service.category || 'N/A'}</div>
                                      <div><strong>Pricing Model:</strong> {service.pricing_model || 'monthly'}</div>
                                      <div><strong>SKU/Tier:</strong> {detailedSKU}</div>
                                      {replicas && replicas > 1 && (
                                        <div><strong>Replicas:</strong> {replicas}</div>
                                      )}
                                      {archService?.configuration?.storage_gb && (
                                        <div><strong>Storage:</strong> {archService.configuration.storage_gb} GB</div>
                                      )}
                                      {archService?.configuration?.auto_scaling && (
                                        <div><strong>Auto-scaling:</strong> Enabled</div>
                                      )}
                                      <div><strong>Region:</strong> {architecture?.region || 'Not specified'}</div>
                                    </div>
                                  </div>
                                  {service.pricing_url && (
                                    <div className="col-span-2 mt-2">
                                      <a 
                                        href={service.pricing_url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-800 underline text-xs"
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        🔗 View Official Pricing Documentation
                                      </a>
                                    </div>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td colSpan={2} className="px-4 py-3 text-sm font-bold text-gray-900">
                        Total (Medium Usage)
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-bold text-blue-600">
                        ${costEstimate.total_monthly_cost_medium?.toFixed(2) || '0.00'}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-bold text-gray-900">
                        100%
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500 mt-4">Currency: {costEstimate.currency} | Period: {costEstimate.time_period}</p>
        </div>
      )}

      {/* Documentation Section */}
      {documentation && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">📝 High-Level Design Document</h2>
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
              {documentation.content}
            </pre>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => {
                const blob = new Blob([documentation.content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'architecture-hld.md';
                a.click();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Download Markdown
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // Render error state
  const renderError = () => (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">❌</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Invalid Request</h2>
          <div className="text-left max-w-xl mx-auto mb-6 space-y-3">
            {error?.split('\n\n').map((paragraph, idx) => (
              <p key={idx} className="text-gray-700 whitespace-pre-line">
                {paragraph}
              </p>
            ))}
          </div>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );

  // Render validating state
  const renderValidating = () => (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-4xl">🔍</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Validating Request</h2>
          <p className="text-gray-600">
            Checking if your request is architecture-related...
          </p>
        </div>
      </div>
    </div>
  );

  // Main render
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      {state === 'initial' && renderInitialForm()}
      {state === 'validating' && renderValidating()}
      {state === 'gathering' && renderGathering()}
      {state === 'ready' && renderReady()}
      {state === 'generating' && renderGenerating()}
      {state === 'complete' && renderComplete()}
      {state === 'error' && renderError()}
    </div>
  );
};

export default KGWizard;
