import React from 'react';
import { CheckCircle2, AlertCircle, XCircle, Loader2 } from 'lucide-react';

interface ReadinessIndicatorProps {
  readyForDesign: boolean;
  criticalGaps: number;
  conflicts: number;
  overallConfidence: number;
}

const ReadinessIndicator: React.FC<ReadinessIndicatorProps> = ({
  readyForDesign,
  criticalGaps,
  conflicts,
  overallConfidence,
}) => {
  const getStatusIcon = () => {
    if (readyForDesign) {
      return <CheckCircle2 className="w-12 h-12 text-green-500" />;
    } else if (criticalGaps === 0 && conflicts === 0) {
      return <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />;
    } else if (conflicts > 0) {
      return <XCircle className="w-12 h-12 text-red-500" />;
    } else {
      return <AlertCircle className="w-12 h-12 text-yellow-500" />;
    }
  };

  const getStatusText = (): string => {
    if (readyForDesign) {
      return 'Ready for Architecture Design';
    } else if (criticalGaps === 0 && conflicts === 0) {
      return 'Gathering Requirements...';
    } else if (conflicts > 0) {
      return 'Conflicts Detected';
    } else {
      return 'Incomplete Requirements';
    }
  };

  const getStatusDescription = (): string => {
    if (readyForDesign) {
      return 'All requirements have been collected successfully. You can now generate the architecture design.';
    } else if (conflicts > 0 && criticalGaps > 0) {
      return `You have ${conflicts} conflict(s) and ${criticalGaps} critical gap(s) that need to be addressed before proceeding.`;
    } else if (conflicts > 0) {
      return `You have ${conflicts} conflict(s) that need to be resolved before proceeding.`;
    } else if (criticalGaps > 0) {
      return `You have ${criticalGaps} critical requirement(s) that need to be answered before proceeding.`;
    } else {
      return 'Continue answering questions to reach the required confidence level.';
    }
  };

  const getBackgroundColor = (): string => {
    if (readyForDesign) {
      return 'bg-green-50 border-green-300';
    } else if (conflicts > 0) {
      return 'bg-red-50 border-red-300';
    } else if (criticalGaps > 0) {
      return 'bg-yellow-50 border-yellow-300';
    } else {
      return 'bg-blue-50 border-blue-300';
    }
  };

  const confidencePercentage = Math.round(overallConfidence * 100);
  const confidenceColor =
    confidencePercentage >= 80
      ? 'text-green-600'
      : confidencePercentage >= 50
      ? 'text-yellow-600'
      : 'text-red-600';

  return (
    <div className={`border-2 rounded-lg p-6 ${getBackgroundColor()}`}>
      {/* Status Header */}
      <div className="flex items-start space-x-4 mb-4">
        <div className="shrink-0">{getStatusIcon()}</div>
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 mb-1">{getStatusText()}</h3>
          <p className="text-sm text-gray-700">{getStatusDescription()}</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        {/* Confidence Score */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Overall Confidence</p>
          <p className={`text-2xl font-bold ${confidenceColor}`}>{confidencePercentage}%</p>
        </div>

        {/* Critical Gaps */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Critical Gaps</p>
          <p
            className={`text-2xl font-bold ${
              criticalGaps === 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {criticalGaps}
          </p>
        </div>

        {/* Conflicts */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Conflicts</p>
          <p
            className={`text-2xl font-bold ${
              conflicts === 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {conflicts}
          </p>
        </div>
      </div>

      {/* Readiness Checklist */}
      <div className="mt-4 pt-4 border-t border-gray-300">
        <p className="text-sm font-medium text-gray-700 mb-2">Readiness Checklist:</p>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            {overallConfidence >= 0.8 ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-gray-400" />
            )}
            <span className="text-sm text-gray-700">
              Confidence ≥ 80% (current: {confidencePercentage}%)
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {criticalGaps === 0 ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-gray-400" />
            )}
            <span className="text-sm text-gray-700">
              No critical gaps (current: {criticalGaps})
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {conflicts === 0 ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-gray-400" />
            )}
            <span className="text-sm text-gray-700">
              No conflicts (current: {conflicts})
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReadinessIndicator;
