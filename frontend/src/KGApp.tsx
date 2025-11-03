import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import KGWizard from './components/KGWizard';
import './App.css';

/**
 * Simple App to demonstrate the Knowledge Graph Wizard
 * 
 * This is a minimal example showing how to integrate the KG Wizard.
 * To use this, replace your App.tsx with this file or integrate the routing.
 */
function KGApp() {
  const [showWizard, setShowWizard] = useState(false);

  if (showWizard) {
    return <KGWizard onBack={() => setShowWizard(false)} />;
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-12">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-600 rounded-full mb-6">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Co-Pilot SE
          </h1>
          
          <p className="text-xl text-gray-600 mb-8">
            AI-Powered Cloud Architecture Assistant
          </p>

          <div className="space-y-4 mb-8">
            <div className="bg-blue-50 rounded-lg p-4 text-left">
              <h3 className="font-semibold text-gray-900 mb-2">✨ Knowledge Graph Wizard</h3>
              <p className="text-sm text-gray-700">
                Adaptive requirements gathering using AI-powered domain agents. The wizard intelligently asks only the most relevant questions based on your initial input.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 text-left">
              <h3 className="font-semibold text-gray-900 mb-2">🎯 Key Features</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Multi-cloud support (AWS, Azure, GCP, Oracle)</li>
                <li>• 6 domain agents (Identity, Runtime, Networking, Data, Resiliency, Security)</li>
                <li>• Real-time conflict detection</li>
                <li>• 80% confidence threshold for design readiness</li>
              </ul>
            </div>
          </div>

          <button
            onClick={() => setShowWizard(true)}
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-lg font-medium inline-flex items-center space-x-2 transition-colors"
          >
            <Sparkles className="w-6 h-6" />
            <span>Start Knowledge Graph Wizard</span>
          </button>

          <p className="text-sm text-gray-500 mt-6">
            Version 2.0 • Multi-Cloud POC
          </p>
        </div>
      </div>
    </div>
  );
}

export default KGApp;
