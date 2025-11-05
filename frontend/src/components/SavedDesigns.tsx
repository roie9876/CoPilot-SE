import { useState, useEffect } from 'react';
import { Folder, Trash2, Eye, X } from 'lucide-react';
import type { ArchitectureOutput, CostOutput, DocumentationOutput, OrchestratorOutput } from '../types';

interface SavedDesign {
  id: number;
  timestamp: string;
  name: string;
  architecture: ArchitectureOutput;
  costs?: CostOutput;
  documentation?: DocumentationOutput;
}

interface SavedDesignsProps {
  onLoadDesign: (result: OrchestratorOutput) => void;
  onClose: () => void;
}

export default function SavedDesigns({ onLoadDesign, onClose }: SavedDesignsProps) {
  const [savedDesigns, setSavedDesigns] = useState<SavedDesign[]>([]);

  useEffect(() => {
    loadSavedDesigns();
  }, []);

  const loadSavedDesigns = () => {
    const designs = JSON.parse(localStorage.getItem('copilot-se-designs') || '[]');
    setSavedDesigns(designs);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this design?')) {
      const designs = savedDesigns.filter(d => d.id !== id);
      localStorage.setItem('copilot-se-designs', JSON.stringify(designs));
      setSavedDesigns(designs);
    }
  };

  const handleLoad = (design: SavedDesign) => {
    console.log('Loading design:', design);
    console.log('Has costs:', !!design.costs);
    console.log('Has documentation:', !!design.documentation);
    
    // Show warning if design is incomplete
    const missingParts = [];
    if (!design.costs) missingParts.push('Cost Analysis');
    if (!design.documentation) missingParts.push('Documentation');
    
    if (missingParts.length > 0) {
      alert(`⚠️ This design is missing: ${missingParts.join(', ')}\n\nThis design was saved before the complete workflow was added.\nPlease generate a new design through the wizard to get full cost and documentation.`);
    }
    
    const stages = ['architecture'];
    if (design.costs) stages.push('cost');
    if (design.documentation) stages.push('documentation');
    
    const result: OrchestratorOutput = {
      status: 'success',
      architecture: design.architecture,
      costs: design.costs,
      documentation: design.documentation,
      citations: design.architecture.citations || [],
      workflow_metadata: {
        stages_completed: stages,
        total_duration_seconds: 0,
        agents_invoked: stages,
        start_time: design.timestamp,
        end_time: design.timestamp
      },
      errors: []
    };
    onLoadDesign(result);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Folder className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Saved Designs
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {savedDesigns.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Folder className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No saved designs yet</p>
              <p className="text-sm mt-2">Save a design to see it here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {savedDesigns.map((design) => (
                <div
                  key={design.id}
                  className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {design.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Saved: {new Date(design.timestamp).toLocaleString()}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                        <span>{design.architecture.services.length} services</span>
                        <span>•</span>
                        <span>{design.architecture.region}</span>
                        <span>•</span>
                        <span>{design.architecture.target_cloud}</span>
                        {design.costs && (
                          <>
                            <span>•</span>
                            <span>Cost: ${design.costs.total_monthly_cost_medium.toFixed(0)}/mo</span>
                          </>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 text-xs text-gray-400 mt-1">
                        {design.costs ? (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                            Cost Analysis ✓
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                            No Cost Data
                          </span>
                        )}
                        {design.documentation ? (
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                            HLD Document ✓
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                            No Documentation
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => handleLoad(design)}
                        className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        title="Load design"
                      >
                        <Eye className="w-4 h-4" />
                        <span>Load</span>
                      </button>
                      <button
                        onClick={() => handleDelete(design.id)}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                        title="Delete design"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
