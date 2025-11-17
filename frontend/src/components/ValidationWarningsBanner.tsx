import { AlertTriangle } from 'lucide-react';

interface ValidationWarningsBannerProps {
  warnings?: string[];
  className?: string;
}

export function ValidationWarningsBanner({ warnings, className }: ValidationWarningsBannerProps) {
  if (!warnings || warnings.length === 0) {
    return null;
  }

  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 ${className || ''}`}>
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600 mt-1" />
        <div>
          <p className="text-sm font-semibold text-yellow-900">
            Azure validation warnings
          </p>
          <p className="text-sm text-yellow-800 mt-1">
            Some services were normalized to approved Azure offerings. Review these notes before proceeding.
          </p>
          <ul className="list-disc list-inside mt-2 text-sm text-yellow-900 space-y-1">
            {warnings.map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
