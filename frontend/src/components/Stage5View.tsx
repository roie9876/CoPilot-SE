import React from 'react';
import type { StageOutput } from '../types';
import { StageApproval } from './StageApproval';
import './Stage5View.css';
import { ValidationWarningsBanner } from './ValidationWarningsBanner';

interface Stage5ViewProps {
  stageOutput: StageOutput;
  sessionId: string;
  stagesCompleted: string[];
  onApprove: () => void;
  onModify?: (modificationRequest: string) => void;
  onBack?: () => void;
  onSeeAlternatives?: () => void;
  isLoading: boolean;
  validationWarnings?: string[];
}

export const Stage5View: React.FC<Stage5ViewProps> = ({
  stageOutput,
  stagesCompleted,
  onApprove,
  onBack,
  isLoading,
  validationWarnings,
}) => {
  return (
    <div className="stage5-view">
      {/* Stage Header */}
      <div className="stage-header final-review-header">
        <div className="review-icon">🎯</div>
        <h2>{stageOutput.stage_title}</h2>
        <p className="stage-description">{stageOutput.stage_description}</p>
      </div>

      <ValidationWarningsBanner warnings={validationWarnings} />

      {/* Chain of Thought - Executive Summary */}
      {stageOutput.chain_of_thought && (
        <div className="executive-summary">
          <div className="summary-icon">💭</div>
          <div className="summary-content">
            <h3>Executive Summary</h3>
            <p>{stageOutput.chain_of_thought}</p>
          </div>
        </div>
      )}

      {/* All Decisions Made Across Stages */}
      {stageOutput.decisions_made && stageOutput.decisions_made.length > 0 && (
        <div className="decisions-summary">
          <h3>✨ Your Complete Architecture</h3>
          <div className="decisions-list">
            {stageOutput.decisions_made.map((decision, index) => (
              <div key={index} className="decision-item">
                <span className="decision-text">{decision}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Breakdown */}
      {stageOutput.estimated_cost && (
        <div className="final-cost-breakdown">
          <div className="cost-header">
            <h3>💰 Total Estimated Cost</h3>
          </div>
          <div className="cost-amount-large">{stageOutput.estimated_cost}</div>
          <div className="cost-note">
            <span className="info-icon">ℹ️</span>
            <span>This is an estimate. Actual costs may vary based on usage patterns and regional pricing.</span>
          </div>
        </div>
      )}

      {/* Architecture Highlights */}
      {stageOutput.recommendations && stageOutput.recommendations.length > 0 && (
        <div className="architecture-highlights">
          <h3>🏗️ Architecture Highlights</h3>
          {stageOutput.recommendations.map((rec, index) => (
            <div key={index} className="highlight-card">
              <h4>{rec.decision_name}</h4>
              <p className="highlight-recommendation">
                <strong>Selected:</strong> {rec.recommendation}
              </p>
              {rec.reasoning && (
                <p className="highlight-reasoning">{rec.reasoning}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* What Happens Next */}
      <div className="whats-next">
        <h3>🚀 What Happens Next?</h3>
        <div className="next-steps">
          <div className="next-step">
            <span className="step-number">1</span>
            <div className="step-content">
              <h4>Generate Complete Documentation</h4>
              <p>High-level design document with architecture diagrams</p>
            </div>
          </div>
          <div className="next-step">
            <span className="step-number">2</span>
            <div className="step-content">
              <h4>Detailed Cost Analysis</h4>
              <p>Month-by-month cost projections with optimization tips</p>
            </div>
          </div>
          <div className="next-step">
            <span className="step-number">3</span>
            <div className="step-content">
              <h4>Implementation Roadmap</h4>
              <p>Step-by-step deployment guide with infrastructure-as-code templates</p>
            </div>
          </div>
        </div>
      </div>

      {/* Final Approval */}
      <div className="final-approval-section">
        <div className="approval-message">
          <p><strong>Ready to proceed?</strong> Click "Generate Complete Architecture" below to create your comprehensive solution design.</p>
        </div>
        <StageApproval
          onApprove={() => onApprove()}
          onBack={onBack}
          isLoading={isLoading}
          canGoBack={stagesCompleted.length > 0}
          canProceed={stageOutput.can_proceed}
          requiresApproval={stageOutput.requires_approval}
          hasAlternatives={false}
          stageName="Final Review"
        />
      </div>
    </div>
  );
};
