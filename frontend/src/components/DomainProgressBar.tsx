import React from 'react';
import { CheckCircle2, Circle, AlertCircle } from 'lucide-react';
import type { DomainConfidence } from '../types-kg';
import { DOMAIN_NAMES, DOMAIN_COLORS } from '../types-kg';

interface DomainProgressBarProps {
  domainConfidence: DomainConfidence;
  currentDomain: string | null;
  readyForDesign: boolean;
}

const DomainProgressBar: React.FC<DomainProgressBarProps> = ({
  domainConfidence,
  currentDomain,
  readyForDesign,
}) => {
  const domains = [
    'identity',
    'runtime',
    'networking',
    'data',
    'resiliency',
    'security',
  ] as const;

  const getStatusIcon = (confidence: number) => {
    if (confidence >= 0.8) {
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    } else if (confidence > 0 && confidence < 0.8) {
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    } else {
      return <Circle className="w-5 h-5 text-gray-300" />;
    }
  };

  const getConfidenceText = (confidence: number): string => {
    if (confidence >= 0.8) return 'Complete';
    if (confidence > 0.5) return 'In Progress';
    if (confidence > 0) return 'Started';
    return 'Not Started';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence > 0.5) return 'text-yellow-600';
    if (confidence > 0) return 'text-blue-600';
    return 'text-gray-400';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">Requirements Gathering Progress</h2>
        {readyForDesign && (
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            Ready for Design
          </span>
        )}
      </div>

      <div className="space-y-4">
        {domains.map((domain) => {
          const confidence = domainConfidence[domain] || 0;
          const isActive = currentDomain === `${domain}_access` || currentDomain === `${domain}_platform` || currentDomain === `${domain}_connectivity` || currentDomain === `${domain}_persistence` || currentDomain === `${domain}_dr` || currentDomain === `${domain}_governance`;
          const domainColor = DOMAIN_COLORS[domain];

          return (
            <div
              key={domain}
              className={`flex items-center space-x-4 p-3 rounded-lg transition-all ${
                isActive ? 'bg-blue-50 border-2 border-blue-300' : 'bg-gray-50'
              }`}
            >
              {/* Icon */}
              <div className="shrink-0">
                {getStatusIcon(confidence)}
              </div>

              {/* Domain Name */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-900">
                    {DOMAIN_NAMES[domain]}
                  </span>
                  <span className={`text-xs font-medium ${getConfidenceColor(confidence)}`}>
                    {getConfidenceText(confidence)}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${confidence * 100}%`,
                      backgroundColor: domainColor,
                    }}
                  />
                </div>
              </div>

              {/* Percentage */}
              <div className="shrink-0 text-sm font-medium text-gray-600">
                {Math.round(confidence * 100)}%
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Progress */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Confidence</span>
          <span className="text-sm font-bold text-gray-900">
            {Math.round(
              (Object.values(domainConfidence).reduce((sum, val) => sum + val, 0) /
                Object.values(domainConfidence).length) *
                100
            )}
            %
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-linear-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
            style={{
              width: `${
                (Object.values(domainConfidence).reduce((sum, val) => sum + val, 0) /
                  Object.values(domainConfidence).length) *
                100
              }%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default DomainProgressBar;
