import React from 'react';
import { AlertTriangle, XCircle, AlertCircle, Info } from 'lucide-react';
import type { Conflict } from '../types-kg';
import { DOMAIN_NAMES } from '../types-kg';

interface ConflictResolutionPanelProps {
  conflicts: Conflict[];
}

const ConflictResolutionPanel: React.FC<ConflictResolutionPanelProps> = ({ conflicts }) => {
  if (conflicts.length === 0) {
    return null;
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-6 h-6 text-red-600" />;
      case 'high':
        return <AlertTriangle className="w-6 h-6 text-orange-500" />;
      case 'medium':
        return <AlertCircle className="w-6 h-6 text-yellow-500" />;
      case 'low':
        return <Info className="w-6 h-6 text-blue-500" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <span className="px-3 py-1 text-xs font-bold bg-red-100 text-red-800 rounded-full uppercase">
            Critical
          </span>
        );
      case 'high':
        return (
          <span className="px-3 py-1 text-xs font-bold bg-orange-100 text-orange-800 rounded-full uppercase">
            High
          </span>
        );
      case 'medium':
        return (
          <span className="px-3 py-1 text-xs font-bold bg-yellow-100 text-yellow-800 rounded-full uppercase">
            Medium
          </span>
        );
      case 'low':
        return (
          <span className="px-3 py-1 text-xs font-bold bg-blue-100 text-blue-800 rounded-full uppercase">
            Low
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 text-xs font-bold bg-gray-100 text-gray-600 rounded-full uppercase">
            Unknown
          </span>
        );
    }
  };

  const getBorderColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'border-red-300';
      case 'high':
        return 'border-orange-300';
      case 'medium':
        return 'border-yellow-300';
      case 'low':
        return 'border-blue-300';
      default:
        return 'border-gray-300';
    }
  };

  const getBackgroundColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50';
      case 'high':
        return 'bg-orange-50';
      case 'medium':
        return 'bg-yellow-50';
      case 'low':
        return 'bg-blue-50';
      default:
        return 'bg-gray-50';
    }
  };

  const formatDomainName = (domain: string): string => {
    const cleanDomain = domain.replace(
      /_access|_platform|_connectivity|_persistence|_dr|_governance/,
      ''
    );
    return DOMAIN_NAMES[cleanDomain as keyof typeof DOMAIN_NAMES] || domain;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center space-x-2 mb-4">
        <AlertTriangle className="w-6 h-6 text-orange-500" />
        <h2 className="text-xl font-bold text-gray-800">
          Conflicts Detected ({conflicts.length})
        </h2>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        The following conflicts were detected in your requirements. Please review and resolve them
        before generating the architecture.
      </p>

      <div className="space-y-4">
        {conflicts.map((conflict) => (
          <div
            key={conflict.id}
            className={`border-2 rounded-lg p-4 ${getBorderColor(
              conflict.severity
            )} ${getBackgroundColor(conflict.severity)}`}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3 flex-1">
                <div className="shrink-0 mt-0.5">{getSeverityIcon(conflict.severity)}</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 mb-1">
                    {conflict.description}
                  </p>
                </div>
              </div>
              <div className="shrink-0 ml-4">{getSeverityBadge(conflict.severity)}</div>
            </div>

            {/* Affected Domains */}
            <div className="flex items-center space-x-2 text-xs text-gray-600 flex-wrap gap-2">
              <span className="font-medium">Affected Domains:</span>
              {conflict.domains.map((domain) => (
                <span
                  key={domain}
                  className="px-2 py-1 bg-white border border-gray-300 rounded text-gray-700"
                >
                  {formatDomainName(domain)}
                </span>
              ))}
            </div>

            {/* Detected At */}
            {conflict.detected_at && (
              <p className="text-xs text-gray-500 mt-2">
                Detected: {new Date(conflict.detected_at).toLocaleString()}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Resolution Note */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">How to resolve conflicts:</p>
            <ul className="list-disc list-inside space-y-1 text-blue-700">
              <li>Review the conflicting requirements in the affected domains</li>
              <li>Adjust your answers to remove contradictions</li>
              <li>Critical and high severity conflicts must be resolved before proceeding</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConflictResolutionPanel;
