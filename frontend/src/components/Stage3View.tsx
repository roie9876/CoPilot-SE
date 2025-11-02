import React, { useState, useEffect } from 'react';
import type { StageOutput } from '../types';
import { StageApproval } from './StageApproval';
import './Stage3View.css';

interface Stage3ViewProps {
  stageOutput: StageOutput;
  sessionId: string;
  stagesCompleted: string[];
  onApprove: (selectedOptions?: Record<string, string>) => void;
  onModify?: (modificationRequest: string) => void;
  onBack?: () => void;
  onSeeAlternatives?: () => void;
  isLoading: boolean;
}

export const Stage3View: React.FC<Stage3ViewProps> = ({
  stageOutput,
  stagesCompleted,
  onApprove,
  onModify,
  onBack,
  onSeeAlternatives,
  isLoading,
}) => {
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});

  // Initialize with AI recommendations
  useEffect(() => {
    const initial: Record<string, string> = {};
    stageOutput.recommendations.forEach(rec => {
      const recommended = rec.trade_offs.find(t => t.recommended);
      if (recommended) {
        initial[rec.decision_name] = recommended.option_name;
      }
    });
    setSelectedOptions(initial);
  }, [stageOutput.recommendations]);

  const handleOptionSelect = (decisionName: string, optionName: string) => {
    setSelectedOptions(prev => ({
      ...prev,
      [decisionName]: optionName
    }));
  };

  return (
    <div className="stage3-view">
      {/* Stage Header */}
      <div className="stage-header">
        <h2>{stageOutput.stage_title}</h2>
        <p className="stage-description">{stageOutput.stage_description}</p>
      </div>

      {/* Chain of Thought */}
      {stageOutput.chain_of_thought && (
        <div className="chain-of-thought">
          <div className="thought-icon">💭</div>
          <div className="thought-content">
            <h3>AI Reasoning</h3>
            <p>{stageOutput.chain_of_thought}</p>
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="recommendations-section">
        {stageOutput.recommendations.map((recommendation, index) => (
          <div key={index} className="recommendation-block">
            {/* Decision Header */}
            <div className="decision-header">
              <h3 className="decision-name">{recommendation.decision_name}</h3>
              <div className="ai-recommendation-badge">
                <span className="badge-icon">🤖</span>
                <span className="badge-text">AI Recommends: {recommendation.recommendation}</span>
              </div>
            </div>

            {/* Reasoning */}
            <div className="reasoning-box">
              <h4>Why This Choice?</h4>
              <p>{recommendation.reasoning}</p>
              {recommendation.cost_impact && (
                <div className="cost-badge">
                  <span className="cost-icon">💰</span>
                  <span className="cost-text">{recommendation.cost_impact}</span>
                </div>
              )}
            </div>

            {/* Trade-offs Grid */}
            <div className="tradeoffs-section">
              <h4>Compare Options</h4>
              <div className="tradeoffs-grid">
                {recommendation.trade_offs.map((tradeoff, tIndex) => (
                  <button
                    key={tIndex}
                    className={`tradeoff-card ${
                      selectedOptions[recommendation.decision_name] === tradeoff.option_name
                        ? 'selected'
                        : ''
                    } ${tradeoff.recommended ? 'ai-recommended' : ''}`}
                    onClick={() => handleOptionSelect(recommendation.decision_name, tradeoff.option_name)}
                  >
                    {/* Card Header */}
                    <div className="card-header">
                      <h5>{tradeoff.option_name}</h5>
                      <div className="badges">
                        {tradeoff.recommended && (
                          <span className="badge ai-badge">AI Pick</span>
                        )}
                        {selectedOptions[recommendation.decision_name] === tradeoff.option_name && (
                          <span className="badge selected-badge">✓ Selected</span>
                        )}
                      </div>
                    </div>

                    {/* Cost & Performance */}
                    <div className="metrics">
                      {tradeoff.cost_impact && (
                        <div className="metric">
                          <span className="metric-label">Cost:</span>
                          <span className="metric-value">{tradeoff.cost_impact}</span>
                        </div>
                      )}
                      {tradeoff.performance_impact && (
                        <div className="metric">
                          <span className="metric-label">Performance:</span>
                          <span className="metric-value">{tradeoff.performance_impact}</span>
                        </div>
                      )}
                    </div>

                    {/* Pros */}
                    <div className="pros-cons-section">
                      <div className="pros">
                        <h6>Pros</h6>
                        <ul>
                          {tradeoff.pros.map((pro, pIndex) => (
                            <li key={pIndex}>
                              <span className="check-icon">✓</span>
                              {pro}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Cons */}
                      <div className="cons">
                        <h6>Cons</h6>
                        <ul>
                          {tradeoff.cons.map((con, cIndex) => (
                            <li key={cIndex}>
                              <span className="x-icon">✗</span>
                              {con}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Alternatives */}
            {recommendation.alternatives && recommendation.alternatives.length > 0 && (
              <div className="alternatives-box">
                <h4>Other Options to Consider</h4>
                <ul className="alternatives-list">
                  {recommendation.alternatives.map((alt, aIndex) => (
                    <li key={aIndex}>{alt}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Dependencies */}
            {recommendation.dependencies && recommendation.dependencies.length > 0 && (
              <div className="dependencies-box">
                <h4>Based On</h4>
                <ul className="dependencies-list">
                  {recommendation.dependencies.map((dep, dIndex) => (
                    <li key={dIndex}>
                      <span className="dep-icon">🔗</span>
                      {dep}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Cost Summary */}
      {stageOutput.estimated_cost && (
        <div className="cost-summary">
          <div className="cost-icon">💵</div>
          <div className="cost-details">
            <h3>Running Total</h3>
            <p className="cost-amount">{stageOutput.estimated_cost}</p>
          </div>
        </div>
      )}

      {/* Stage Approval Actions */}
      <StageApproval
        onApprove={() => onApprove(selectedOptions)}
        onModify={onModify}
        onBack={onBack}
        onSeeAlternatives={onSeeAlternatives}
        isLoading={isLoading}
        canGoBack={stagesCompleted.length > 0}
        canProceed={stageOutput.can_proceed}
        requiresApproval={stageOutput.requires_approval}
        hasAlternatives={stageOutput.recommendations.some(r => r.alternatives && r.alternatives.length > 0)}
        stageName={stageOutput.stage_title}
      />
    </div>
  );
};
