import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { Server, Package, DollarSign, AlertCircle } from 'lucide-react';
import type { ArchitectureOutput } from '../types';

interface ArchitectureViewProps {
  architecture: ArchitectureOutput;
}

// Initialize mermaid
mermaid.initialize({ 
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: { curve: 'basis' }
});

export default function ArchitectureView({ architecture }: ArchitectureViewProps) {
  const diagramRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      if (diagramRef.current && architecture.architecture_diagram) {
        // Clear previous content
        diagramRef.current.innerHTML = '';
        
        // Strip markdown code fence if present (```mermaid ... ```)
        let diagramCode = architecture.architecture_diagram.trim();
        if (diagramCode.startsWith('```mermaid')) {
          diagramCode = diagramCode.replace(/^```mermaid\n/, '').replace(/\n```$/, '');
        } else if (diagramCode.startsWith('```')) {
          diagramCode = diagramCode.replace(/^```\n/, '').replace(/\n```$/, '');
        }
        
        // Fix common Mermaid syntax errors from backend
        // 1. Add missing newlines between statements (e.g., "]B -->" should be "]\nB -->")
        diagramCode = diagramCode.replace(/\]([A-Z][A-Z0-9]*)\s+(-->|---)/g, ']\n$1 $2');
        
        // 2. Fix parentheses in labels - wrap entire label in quotes if it contains parentheses
        diagramCode = diagramCode.replace(/\[([^\]]*\([^\]]*\)[^\]]*)\]/g, (match, label) => {
          // If label doesn't already have quotes, add them
          if (!label.startsWith('"') && !label.endsWith('"')) {
            return `["${label}"]`;
          }
          return match;
        });
        
        // 3. Remove trailing whitespace from each line
        diagramCode = diagramCode.split('\n').map(line => line.trimEnd()).join('\n');
        
        // 4. Fix unclosed brackets in node definitions
        const lines = diagramCode.split('\n');
        const fixedLines = lines.map((line, index) => {
          // Skip empty lines and graph declaration
          if (!line.trim() || line.trim().startsWith('graph ')) {
            return line;
          }
          
          // Count only the square brackets used for node shapes, not in strings
          // Simple heuristic: don't count brackets inside quotes
          const withoutQuotes = line.replace(/"[^"]*"/g, '');
          const openBrackets = (withoutQuotes.match(/\[/g) || []).length;
          const closeBrackets = (withoutQuotes.match(/\]/g) || []).length;
          
          if (openBrackets > closeBrackets) {
            const missing = openBrackets - closeBrackets;
            console.log(`Line ${index + 1} missing ${missing} closing bracket(s): ${line.substring(0, 60)}`);
            // Add missing closing brackets at the end of the line
            return line.trimEnd() + ']'.repeat(missing);
          }
          return line;
        });
        diagramCode = fixedLines.join('\n');
        
        console.log('Final processed diagram:', diagramCode);
        
        try {
          // Generate unique ID for this diagram
          const id = `mermaid-${Date.now()}`;
          
          // Render mermaid diagram
          const { svg } = await mermaid.render(id, diagramCode);
          
          // Insert rendered SVG
          diagramRef.current.innerHTML = svg;
        } catch (error) {
          console.error('Mermaid rendering error:', error);
          console.log('Original diagram code:', architecture.architecture_diagram);
          console.log('Processed diagram code:', diagramCode);
          // Fallback to showing a helpful error message and the code
          diagramRef.current.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p class="text-yellow-800 font-semibold mb-2">⚠️ Unable to render diagram</p>
              <p class="text-yellow-700 text-sm">The backend generated invalid Mermaid syntax. Showing raw code below:</p>
            </div>
            <pre class="text-sm text-gray-800 bg-gray-100 p-4 rounded overflow-x-auto whitespace-pre-wrap">${diagramCode}</pre>
          `;
        }
      }
    };
    
    renderDiagram();
  }, [architecture.architecture_diagram]);

  return (
    <div className="space-y-6">
      {/* Architecture Diagram */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Package className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            Architecture Diagram
          </h3>
        </div>
        <div 
          ref={diagramRef}
          className="mermaid bg-white dark:bg-gray-900 p-4 rounded-lg overflow-x-auto"
        />
        {architecture.citations && architecture.citations.length > 0 && (
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            <p className="font-medium mb-2">References:</p>
            <ul className="list-disc list-inside space-y-1">
              {architecture.citations.slice(0, 3).map((citation, index) => (
                <li key={index}>
                  <a 
                    href={citation.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {citation.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Services Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Server className="w-6 h-6 text-green-600" />
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            Selected Services ({architecture.services.length})
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Service</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Category</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Rationale</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Est. Cost/Month</th>
              </tr>
            </thead>
            <tbody>
              {architecture.services.map((service, index) => (
                <tr key={index} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="py-3 px-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{service.service_name}</div>
                      {service.configuration && Object.keys(service.configuration).length > 0 && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {Object.entries(service.configuration).slice(0, 2).map(([key, value]) => (
                            <span key={key} className="mr-2">{key}: {String(value)}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                      {service.category}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{service.rationale}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-1 text-green-600 dark:text-green-400 font-medium">
                      <DollarSign className="w-4 h-4" />
                      <span>{service.estimated_monthly_cost != null ? service.estimated_monthly_cost.toFixed(2) : 'N/A'}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Design Rationale - Well-Architected Framework Pillars */}
      {architecture.design_rationale && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Design Rationale (Well-Architected Framework)
          </h3>
          <div className="space-y-3">
            {Object.entries(architecture.design_rationale).map(([pillar, description]) => (
              <div key={pillar} className="flex items-start space-x-3">
                <div className="flex-shrink-0 px-2 py-1 rounded bg-blue-100 dark:bg-blue-900">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-300 uppercase">
                    {pillar.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-gray-700 dark:text-gray-300">{description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deployment Considerations */}
      {architecture.deployment_considerations && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <AlertCircle className="w-6 h-6 text-yellow-600" />
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              Deployment Considerations
            </h3>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Region:</span>
                <p className="text-gray-900 dark:text-white">{architecture.deployment_considerations.region}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Multi-AZ:</span>
                <p className="text-gray-900 dark:text-white">{architecture.deployment_considerations.multi_az ? 'Yes' : 'No'}</p>
              </div>
            </div>
            
            {architecture.deployment_considerations.prerequisites && architecture.deployment_considerations.prerequisites.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400 block mb-2">Prerequisites:</span>
                <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                  {architecture.deployment_considerations.prerequisites.map((prereq, index) => (
                    <li key={index}>{prereq}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {architecture.deployment_considerations.deployment_methods && architecture.deployment_considerations.deployment_methods.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400 block mb-2">Deployment Methods:</span>
                <div className="flex flex-wrap gap-2">
                  {architecture.deployment_considerations.deployment_methods.map((method, index) => (
                    <span key={index} className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded text-sm">
                      {method}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <div>
              <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Estimated Deployment Time:</span>
              <p className="text-gray-900 dark:text-white">{architecture.deployment_considerations.estimated_deployment_time}</p>
            </div>
          </div>
        </div>
      )}

      {/* Technology Stack */}
      {architecture.technology_stack && architecture.technology_stack.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Technology Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            {architecture.technology_stack.map((tech, index) => (
              <span 
                key={index}
                className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full text-sm font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
