import { useState } from 'react';
import { Loader2, Cloud, FileText, DollarSign, CheckCircle2 } from 'lucide-react';
import ArchitectureView from './components/ArchitectureView';
import CostView from './components/CostView';
import DocumentationView from './components/DocumentationView';
import ClarificationView from './components/ClarificationView';
import { Stage1View } from './components/Stage1View';
import { Stage2View } from './components/Stage2View';
import { Stage3View } from './components/Stage3View';
import { Stage4View } from './components/Stage4View';
import { Stage5View } from './components/Stage5View';
import KGWizard from './components/KGWizard';
import type { OrchestratorOutput } from './types';
import { generateArchitecture, submitClarification, approveStage } from './api/client';
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OrchestratorOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'architecture' | 'cost' | 'documentation'>('architecture');
  
  // Legacy clarification state
  const [needsClarification, setNeedsClarification] = useState(false);
  const [clarificationData, setClarificationData] = useState<OrchestratorOutput | null>(null);

  // Multi-stage wizard state
  const [inStageFlow, setInStageFlow] = useState(false);
  const [stageData, setStageData] = useState<OrchestratorOutput | null>(null);
  
  // Progressive multi-turn state
  const [currentRound, setCurrentRound] = useState(1);
  const [loadingMessage, setLoadingMessage] = useState<string>('');

  // Legacy submit handler (kept for reference, not currently used)
  // @ts-expect-error - unused variable kept for reference
  const handleSubmit = async (requirements: string) => {
    console.log('handleSubmit called with:', requirements);
    setLoading(true);
    setError(null);
    setResult(null);
    setNeedsClarification(false);
    setClarificationData(null);
    setInStageFlow(false);
    setStageData(null);
    setCurrentRound(1);
    setLoadingMessage('Generating Round 1 questions...');

    try {
      console.log('Calling generateArchitecture...');
      const data = await generateArchitecture(requirements);
      console.log('Received data:', data);
      
      // Check for multi-stage flow
      if (data.status === 'awaiting_stage_approval' && data.stage_output) {
        console.log('Multi-stage flow detected, showing Stage 1...');
        setInStageFlow(true);
        setStageData(data);
        setCurrentRound(1);
      }
      // Check if clarification is needed (legacy flow)
      else if (data.status === 'needs_clarification') {
        console.log('Clarification needed, showing questions...');
        setNeedsClarification(true);
        setClarificationData(data);
      }
      // Complete result
      else if (data.status === 'success') {
        setResult(data);
      }
      console.log('Result set successfully');
    } catch (err) {
      console.error('Error in handleSubmit:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate architecture');
    } finally {
      setLoading(false);
      console.log('Loading set to false');
    }
  };

  const handleClarificationSubmit = async (answers: Record<string, string>) => {
    if (!clarificationData?.session_id) {
      setError('Session ID not found. Please start over.');
      return;
    }

    console.log('handleClarificationSubmit called with:', answers);
    setLoading(true);
    setError(null);

    try {
      console.log('Submitting clarification answers...');
      const data = await submitClarification(clarificationData.session_id, answers);
      console.log('Received complete data after clarification:', data);
      
      // Should get complete result now
      setResult(data);
      setNeedsClarification(false);
      setClarificationData(null);
    } catch (err) {
      console.error('Error in handleClarificationSubmit:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit clarification');
    } finally {
      setLoading(false);
    }
  };

  const handleStageApproval = async (answers?: Record<string, string>) => {
    if (!stageData?.session_id || !stageData?.conversation_stage) {
      setError('Session data not found. Please start over.');
      return;
    }

    console.log('handleStageApproval called with:', answers);
    setLoading(true);
    setError(null);
    
    // Set appropriate loading message based on stage
    if (stageData.conversation_stage === 'stage_1_requirements') {
      setLoadingMessage('Analyzing your answers...');
    } else {
      setLoadingMessage('Generating recommendations...');
    }

    try {
      console.log('Approving stage:', stageData.conversation_stage);
      const data = await approveStage(
        stageData.session_id,
        stageData.conversation_stage,
        'approve',
        { answers }
      );
      console.log('Received data after stage approval:', data);
      
      // Check if we need to show next stage
      if (data.status === 'awaiting_stage_approval' && data.stage_output) {
        console.log('Moving to next stage:', data.conversation_stage);
        
        // If still in Stage 1, increment round
        if (data.conversation_stage === 'stage_1_requirements') {
          // Check if stage title indicates a round number
          const titleMatch = data.stage_output.stage_title?.match(/Round (\d+)/);
          if (titleMatch) {
            setCurrentRound(parseInt(titleMatch[1]));
          } else {
            setCurrentRound(prev => prev + 1);
          }
        } else {
          // Moving to Stage 2+, reset round
          setCurrentRound(1);
        }
        
        setStageData(data);
      }
      // Complete result
      else if (data.status === 'success') {
        console.log('All stages complete, showing final architecture');
        setResult(data);
        setInStageFlow(false);
        setStageData(null);
        setCurrentRound(1);
      }
    } catch (err) {
      console.error('Error in handleStageApproval:', err);
      setError(err instanceof Error ? err.message : 'Failed to approve stage');
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const handleGoBack = async () => {
    if (!stageData?.session_id || !stageData?.conversation_stage) {
      setError('Session data not found. Please start over.');
      return;
    }

    console.log('handleGoBack called');
    setLoading(true);
    setError(null);

    try {
      const data = await approveStage(
        stageData.session_id,
        stageData.conversation_stage,
        'back'
      );
      console.log('Went back to previous stage:', data.conversation_stage);
      setStageData(data);
    } catch (err) {
      console.error('Error in handleGoBack:', err);
      setError(err instanceof Error ? err.message : 'Failed to go back');
    } finally {
      setLoading(false);
    }
  };

  const handleSeeAlternatives = async () => {
    if (!stageData?.session_id || !stageData?.conversation_stage) {
      setError('Session data not found. Please start over.');
      return;
    }

    console.log('handleSeeAlternatives called');
    setLoading(true);
    setError(null);

    try {
      const data = await approveStage(
        stageData.session_id,
        stageData.conversation_stage,
        'see_alternatives'
      );
      console.log('Showing alternatives for current stage');
      setStageData(data);
    } catch (err) {
      console.error('Error in handleSeeAlternatives:', err);
      setError(err instanceof Error ? err.message : 'Failed to show alternatives');
    } finally {
      setLoading(false);
    }
  };

  const handleModify = async (modificationRequest: string) => {
    if (!stageData?.session_id || !stageData?.conversation_stage) {
      setError('Session data not found. Please start over.');
      return;
    }

    console.log('handleModify called with:', modificationRequest);
    setLoading(true);
    setError(null);

    try {
      const data = await approveStage(
        stageData.session_id,
        stageData.conversation_stage,
        'modify',
        { modification_request: modificationRequest }
      );
      console.log('Modified recommendations for current stage');
      setStageData(data);
    } catch (err) {
      console.error('Error in handleModify:', err);
      setError(err instanceof Error ? err.message : 'Failed to modify recommendations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100" style={{ minHeight: '100vh', background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)' }}>
      {/* Header */}
      <header className="bg-white shadow-md" style={{ backgroundColor: 'white' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Copilot for Solution Architects
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Multi-Cloud Architecture Assistant
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Knowledge Graph Wizard - Default Interface */}
        {!result && !loading && !needsClarification && !inStageFlow && (
          <KGWizard />
        )}

        {/* Multi-Stage Flow */}
        {inStageFlow && stageData && stageData.stage_output && (
          <>
            {stageData.conversation_stage === 'stage_1_requirements' && (
              <Stage1View
                stageOutput={stageData.stage_output}
                sessionId={stageData.session_id || ''}
                onApprove={handleStageApproval}
                isLoading={loading}
                loadingMessage={loadingMessage}
                currentRound={currentRound}
              />
            )}
            {stageData.conversation_stage === 'stage_2_compute' && (
              <Stage2View
                stageOutput={stageData.stage_output}
                sessionId={stageData.session_id || ''}
                stagesCompleted={stageData.stages_completed || []}
                onApprove={handleStageApproval}
                onModify={handleModify}
                onBack={handleGoBack}
                onSeeAlternatives={handleSeeAlternatives}
                isLoading={loading}
              />
            )}
            {stageData.conversation_stage === 'stage_3_data' && (
              <Stage3View
                stageOutput={stageData.stage_output}
                sessionId={stageData.session_id || ''}
                stagesCompleted={stageData.stages_completed || []}
                onApprove={handleStageApproval}
                onModify={handleModify}
                onBack={handleGoBack}
                onSeeAlternatives={handleSeeAlternatives}
                isLoading={loading}
              />
            )}
            {stageData.conversation_stage === 'stage_4_security' && (
              <Stage4View
                stageOutput={stageData.stage_output}
                sessionId={stageData.session_id || ''}
                stagesCompleted={stageData.stages_completed || []}
                onApprove={handleStageApproval}
                onModify={handleModify}
                onBack={handleGoBack}
                onSeeAlternatives={handleSeeAlternatives}
                isLoading={loading}
              />
            )}
            {stageData.conversation_stage === 'stage_5_review' && (
              <Stage5View
                stageOutput={stageData.stage_output}
                sessionId={stageData.session_id || ''}
                stagesCompleted={stageData.stages_completed || []}
                onApprove={handleStageApproval}
                onModify={handleModify}
                onBack={handleGoBack}
                onSeeAlternatives={handleSeeAlternatives}
                isLoading={loading}
              />
            )}
          </>
        )}

        {/* Legacy Clarification View */}
        {needsClarification && clarificationData && !loading && (
          <ClarificationView
            questions={clarificationData.clarifying_questions || []}
            chainOfThought={clarificationData.chain_of_thought}
            decisionsMade={clarificationData.decisions_made}
            currentUnderstanding={clarificationData.current_understanding}
            ambiguities={clarificationData.ambiguities}
            onSubmit={handleClarificationSubmit}
            isSubmitting={loading}
          />
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
              Generating Architecture...
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Our AI agents are analyzing your requirements and designing the optimal solution
            </p>
            <div className="mt-6 space-y-2">
              <div className="flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
                <CheckCircle2 className="w-4 h-4 mr-2 text-green-500" />
                Requirements Analysis
              </div>
              <div className="flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
                <Loader2 className="w-4 h-4 mr-2 animate-spin text-blue-500" />
                Architecture Design
              </div>
              <div className="flex items-center justify-center text-sm text-gray-500 dark:text-gray-400 opacity-50">
                Cost Estimation
              </div>
              <div className="flex items-center justify-center text-sm text-gray-500 dark:text-gray-400 opacity-50">
                Documentation Generation
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-300 mb-2">
              Error
            </h3>
            <p className="text-red-700 dark:text-red-400">{error}</p>
            <button
              onClick={() => {
                setError(null);
                setResult(null);
              }}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-6">
            {/* Tabs */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('architecture')}
                    className={`flex items-center px-6 py-4 text-sm font-medium transition ${
                      activeTab === 'architecture'
                        ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                    }`}
                  >
                    <Cloud className="w-5 h-5 mr-2" />
                    Architecture
                  </button>
                  <button
                    onClick={() => setActiveTab('cost')}
                    className={`flex items-center px-6 py-4 text-sm font-medium transition ${
                      activeTab === 'cost'
                        ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                    }`}
                  >
                    <DollarSign className="w-5 h-5 mr-2" />
                    Cost Analysis
                  </button>
                  <button
                    onClick={() => setActiveTab('documentation')}
                    className={`flex items-center px-6 py-4 text-sm font-medium transition ${
                      activeTab === 'documentation'
                        ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                    }`}
                  >
                    <FileText className="w-5 h-5 mr-2" />
                    Documentation
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="space-y-6">
                {activeTab === 'architecture' && result.architecture && <ArchitectureView architecture={result.architecture} />}
                {activeTab === 'cost' && result.costs && <CostView costs={result.costs} />}
                {activeTab === 'documentation' && result.documentation && <DocumentationView documentation={result.documentation} />}
              </div>
            </div>

            {/* New Design Button */}
            <div className="text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setActiveTab('architecture');
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-lg"
              >
                Create New Design
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 py-6 text-center text-sm text-gray-600 dark:text-gray-400">
        <p>Co-Pilot SE v2.0 - POC Multi-Cloud Architecture Assistant</p>
        <p className="mt-1">Powered by Azure OpenAI GPT-5 & Microsoft Agent Framework</p>
      </footer>
    </div>
  );
}

export default App;
