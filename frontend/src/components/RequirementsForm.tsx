import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface RequirementsFormProps {
  onSubmit: (requirements: string) => void;
  loading: boolean;
}

const EXAMPLE_PROMPTS = [
  "Design an Azure e-commerce platform for 50,000 concurrent users with PCI DSS compliance and $5,000/month budget",
  "Build a serverless API backend on AWS for a mobile app with user authentication and file storage",
  "Create a GCP microservices architecture with Kubernetes for a SaaS application",
  "Design an Oracle Cloud data warehouse solution for analytics with 10TB of data",
];

export default function RequirementsForm({ onSubmit, loading }: RequirementsFormProps) {
  const [requirements, setRequirements] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (requirements.trim().length >= 10) {
      onSubmit(requirements);
    }
  };

  const handleExampleClick = (example: string) => {
    setRequirements(example);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="flex items-center space-x-3 mb-6">
        <Sparkles className="w-8 h-8 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Describe Your Requirements
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            What cloud architecture do you need?
          </label>
          <textarea
            id="requirements"
            rows={5}
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Example: Design an Azure e-commerce platform for 50,000 concurrent users with PCI DSS compliance and $5,000/month budget"
            className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            required
            minLength={10}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Minimum 10 characters. Include cloud platform (Azure/AWS/GCP/Oracle), requirements, constraints, and budget.
          </p>
        </div>

        {/* Submit Button - Moved Above Examples */}
        <div className="flex justify-center pt-2">
          <button
            type="submit"
            disabled={loading || requirements.trim().length < 10}
            style={{
              backgroundColor: loading || requirements.trim().length < 10 ? '#d1d5db' : '#2563eb',
              color: loading || requirements.trim().length < 10 ? '#6b7280' : '#ffffff',
              cursor: loading || requirements.trim().length < 10 ? 'not-allowed' : 'pointer',
            }}
            className="px-8 py-3 rounded-lg transition shadow-lg flex items-center space-x-2 text-lg font-semibold hover:opacity-90"
          >
            <Send className="w-5 h-5" />
            <span>Generate Architecture</span>
          </button>
        </div>

        {/* Example Prompts - Moved Below Button */}
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Or try an example:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {EXAMPLE_PROMPTS.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="text-left px-3 py-2 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
