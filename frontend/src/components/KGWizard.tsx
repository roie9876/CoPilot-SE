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
} from '../types-kg';
import type { ArchitectureOutput } from '../types';
import { kgStart, kgAnswer, kgArchitecture } from '../api/kg-client';

type WizardState =
  | 'initial'
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
  });
  const [readyForDesign, setReadyForDesign] = useState(false);
  const [criticalGaps, setCriticalGaps] = useState(0);
  const [conflictsCount, setConflictsCount] = useState(0);
  const [conflictsDetail, setConflictsDetail] = useState<Conflict[]>([]);
  const [overallConfidence, setOverallConfidence] = useState(0);

  // Architecture result
  const [architecture, setArchitecture] = useState<ArchitectureOutput | null>(null);
  const [costEstimate, setCostEstimate] = useState<any | null>(null);
  const [documentation, setDocumentation] = useState<any | null>(null);

  // Submitting state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Start Knowledge Graph session
  const handleStartSession = async () => {
    if (!requirements.trim()) {
      setError('Please enter your requirements');
      return;
    }

    setState('gathering');
    setError(null);
    setIsSubmitting(true);

    try {
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
            Knowledge Graph Architecture Wizard
          </h1>
        </div>

        <p className="text-gray-600 mb-6">
          Describe your cloud architecture requirements in natural language. Our AI will guide you
          through a series of adaptive questions to gather all necessary information.
        </p>

        <div className="space-y-4">
          <div>
            <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-2">
              Requirements Description
            </label>
            <textarea
              id="requirements"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Example: Build an e-commerce platform on Azure for 10,000 users with high availability..."
              disabled={isSubmitting}
            />
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-red-800">
              {error}
            </div>
          )}

          <div className="flex items-center justify-between">
            {onBack && (
              <button
                onClick={onBack}
                className="px-6 py-3 text-gray-700 hover:text-gray-900 flex items-center space-x-2"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back</span>
              </button>
            )}
            <button
              onClick={handleStartSession}
              disabled={isSubmitting || !requirements.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
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
      {questions.length > 0 && currentDomain && (
        <AdaptiveQuestionForm
          domain={currentDomain}
          questions={questions}
          onSubmit={handleSubmitAnswers}
          isSubmitting={isSubmitting}
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

      {architecture && <ArchitectureView architecture={architecture} />}

      {/* Cost Estimate Section */}
      {costEstimate && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">💰 Cost Estimate</h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
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
          <p className="text-sm text-gray-500">Currency: {costEstimate.currency} | Period: {costEstimate.time_period}</p>
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
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Start Over
          </button>
        </div>
      </div>
    </div>
  );

  // Main render
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      {state === 'initial' && renderInitialForm()}
      {state === 'gathering' && renderGathering()}
      {state === 'ready' && renderReady()}
      {state === 'generating' && renderGenerating()}
      {state === 'complete' && renderComplete()}
      {state === 'error' && renderError()}
    </div>
  );
};

export default KGWizard;
