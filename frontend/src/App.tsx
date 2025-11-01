import { useState } from 'react';
import { Loader2, Cloud, FileText, DollarSign, CheckCircle2 } from 'lucide-react';
import RequirementsForm from './components/RequirementsForm';
import ArchitectureView from './components/ArchitectureView';
import CostView from './components/CostView';
import DocumentationView from './components/DocumentationView';
import { OrchestratorOutput } from './types';
import { generateArchitecture } from './api/client';
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OrchestratorOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'architecture' | 'cost' | 'documentation'>('architecture');

  const handleSubmit = async (requirements: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await generateArchitecture(requirements);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate architecture');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <Cloud className="w-10 h-10 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Co-Pilot SE
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Multi-Cloud Architecture Assistant
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Requirements Form */}
        {!result && !loading && (
          <RequirementsForm onSubmit={handleSubmit} loading={loading} />
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
              <div className="p-6">
                {activeTab === 'architecture' && <ArchitectureView architecture={result.architecture} />}
                {activeTab === 'cost' && <CostView costs={result.costs} />}
                {activeTab === 'documentation' && <DocumentationView documentation={result.documentation} />}
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
