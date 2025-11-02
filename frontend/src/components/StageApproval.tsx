import React, { useState } from 'react';
import './StageApproval.css';

interface StageApprovalProps {
  canGoBack: boolean;
  canProceed: boolean;
  requiresApproval: boolean;
  hasAlternatives: boolean;
  onApprove: () => void;
  onModify?: (modificationRequest: string) => void;
  onBack?: () => void;
  onSeeAlternatives?: () => void;
  isLoading?: boolean;
  stageName: string;
}

export const StageApproval: React.FC<StageApprovalProps> = ({
  canGoBack,
  canProceed,
  requiresApproval,
  hasAlternatives,
  onApprove,
  onModify,
  onBack,
  onSeeAlternatives,
  isLoading = false,
  stageName,
}) => {
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modificationRequest, setModificationRequest] = useState('');

  const handleModifySubmit = () => {
    if (onModify && modificationRequest.trim()) {
      onModify(modificationRequest);
      setShowModifyInput(false);
      setModificationRequest('');
    }
  };

  return (
    <div className="stage-approval">
      {requiresApproval && (
        <div className="approval-message">
          <div className="approval-icon">👇</div>
          <div className="approval-text">
            Please review the recommendations above and choose how to proceed with{' '}
            <strong>{stageName}</strong>
          </div>
        </div>
      )}

      {showModifyInput && (
        <div className="modify-input-section">
          <label className="modify-label">
            What would you like to change about this recommendation?
          </label>
          <textarea
            className="modify-textarea"
            placeholder="Example: I prefer a serverless solution instead... or I need support for multi-region..."
            value={modificationRequest}
            onChange={(e) => setModificationRequest(e.target.value)}
            rows={4}
          />
          <div className="modify-actions">
            <button
              className="modify-submit-button"
              onClick={handleModifySubmit}
              disabled={!modificationRequest.trim()}
            >
              Submit Changes
            </button>
            <button
              className="modify-cancel-button"
              onClick={() => {
                setShowModifyInput(false);
                setModificationRequest('');
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="approval-buttons">
        {canGoBack && onBack && (
          <button
            className="approval-button back-button"
            onClick={onBack}
            disabled={isLoading}
          >
            <span className="button-icon">←</span>
            <span className="button-text">Go Back</span>
          </button>
        )}

        {hasAlternatives && onSeeAlternatives && (
          <button
            className="approval-button alternatives-button"
            onClick={onSeeAlternatives}
            disabled={isLoading}
          >
            <span className="button-icon">🔄</span>
            <span className="button-text">See Alternatives</span>
          </button>
        )}

        {onModify && !showModifyInput && (
          <button
            className="approval-button modify-button"
            onClick={() => setShowModifyInput(true)}
            disabled={isLoading}
          >
            <span className="button-icon">✏️</span>
            <span className="button-text">Modify Decision</span>
          </button>
        )}

        {canProceed && (
          <button
            className="approval-button approve-button"
            onClick={onApprove}
            disabled={isLoading || showModifyInput}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                <span className="button-text">Processing...</span>
              </>
            ) : (
              <>
                <span className="button-text">Approve & Continue</span>
                <span className="button-icon">✓</span>
              </>
            )}
          </button>
        )}
      </div>

      {!canProceed && (
        <div className="warning-message">
          <div className="warning-icon">⚠️</div>
          <div className="warning-text">
            Please answer all questions above before proceeding
          </div>
        </div>
      )}
    </div>
  );
};
