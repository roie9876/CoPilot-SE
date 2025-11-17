import React from 'react';
import { StageProgress } from './StageProgress';
import { StageApproval } from './StageApproval';
import type { StageOutput } from '../types';
import './Stage2View.css';
import { ValidationWarningsBanner } from './ValidationWarningsBanner';

interface Stage2ViewProps {
  stageOutput: StageOutput;
  sessionId: string;
  stagesCompleted: string[];
  onApprove: (selectedOptions?: Record<string, string>) => void;
  onModify?: (modificationRequest: string) => void;
  onBack?: () => void;
  onSeeAlternatives?: () => void;
  isLoading: boolean;
  validationWarnings?: string[];
}

export const Stage2View: React.FC<Stage2ViewProps> = ({
  stageOutput,
  stagesCompleted,
  onApprove,
  onModify,
  onBack,
  onSeeAlternatives,
  isLoading,
  validationWarnings,
}) => {
  const [showReasoning, setShowReasoning] = React.useState(false);
  const [selectedOptions, setSelectedOptions] = React.useState<Record<string, string>>({});

  // Initialize with recommended options
  React.useEffect(() => {
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
    <div className="stage2-view">
      <StageProgress
        currentStage="stage_2_compute"
        stagesCompleted={stagesCompleted}
      />

      <div className="stage-header">
        <h2 className="stage-title">{stageOutput.stage_title}</h2>
        <p className="stage-description">{stageOutput.stage_description}</p>
        {stageOutput.estimated_cost && (
          <div className="running-cost-badge">
            Running Total: {stageOutput.estimated_cost}
          </div>
        )}
      </div>

      <ValidationWarningsBanner warnings={validationWarnings} />

      {stageOutput.chain_of_thought && (
        <div className="chain-of-thought-section">
          <button
            className="cot-toggle"
            onClick={() => setShowReasoning(!showReasoning)}
          >
            <span className="cot-icon">🤔</span>
            <span className="cot-title">AI's Thought Process</span>
            <span className={`toggle-arrow ${showReasoning ? 'open' : ''}`}>▼</span>
          </button>
          {showReasoning && (
            <div className="cot-content">
              <p>{stageOutput.chain_of_thought}</p>
            </div>
          )}
        </div>
      )}

      <div className="recommendations-section">
        {stageOutput.recommendations.map((recommendation, index) => (
          <div key={index}>
            <div className="recommendation-header-with-cost">
              <h3 className="decision-name">{recommendation.decision_name}</h3>
              <div className="cost-badge">{recommendation.cost_impact}</div>
            </div>
            
            {/* AI Recommendation Display */}
            <div className="ai-recommendation-display">
              <div className="recommendation-icon">🎯</div>
              <div className="recommendation-text">
                <div className="recommendation-label">AI RECOMMENDATION</div>
                <div className="recommendation-value">{recommendation.recommendation}</div>
              </div>
            </div>

            {/* Reasoning */}
            <div className="reasoning-section">
              <div className="reasoning-header">
                <span className="reasoning-icon">💡</span>
                <span className="reasoning-title">Why This Recommendation?</span>
              </div>
              <p className="reasoning-text">{recommendation.reasoning}</p>
            </div>

            {/* Trade-off Selection */}
            <div className="tradeoff-section">
              <div className="tradeoff-header">
                <span className="tradeoff-icon">⚖️</span>
                <span className="tradeoff-title">Compare Options & Select Your Preference</span>
              </div>
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
                    <div className="tradeoff-card-header">
                      <h4 className="tradeoff-name">{tradeoff.option_name}</h4>
                      <div className="badges">
                        {tradeoff.recommended && (
                          <span className="ai-badge">AI Pick</span>
                        )}
                        {selectedOptions[recommendation.decision_name] === tradeoff.option_name && (
                          <span className="selected-badge">✓ Selected</span>
                        )}
                      </div>
                    </div>

                    <div className="tradeoff-metrics">
                      <div className="metric">
                        <span className="metric-label">Cost:</span>
                        <span className="metric-value">{tradeoff.cost_impact}</span>
                      </div>
                      {tradeoff.performance_impact && (
                        <div className="metric">
                          <span className="metric-label">Performance:</span>
                          <span className="metric-value">{tradeoff.performance_impact}</span>
                        </div>
                      )}
                    </div>

                    <div className="pros-cons">
                      <div className="pros">
                        <div className="pros-header">✓ Pros</div>
                        <ul>
                          {tradeoff.pros.map((pro, i) => (
                            <li key={i}>{pro}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="cons">
                        <div className="cons-header">✗ Cons</div>
                        <ul>
                          {tradeoff.cons.map((con, i) => (
                            <li key={i}>{con}</li>
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
              <div className="alternatives-section">
                <div className="alternatives-header">
                  <span className="alternatives-icon">🔄</span>
                  <span className="alternatives-title">Other Options</span>
                </div>
                <div className="alternatives-list">
                  {recommendation.alternatives.map((alt, aIndex) => (
                    <div key={aIndex} className="alternative-item">{alt}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {stageOutput.decisions_made && stageOutput.decisions_made.length > 0 && (
        <div className="decisions-summary">
          <h3 className="decisions-title">Decisions Made So Far:</h3>
          <ul className="decisions-list">
            {stageOutput.decisions_made.map((decision, index) => (
              <li key={index}>{decision}</li>
            ))}
          </ul>
        </div>
      )}

      <StageApproval
        canGoBack={true}
        canProceed={stageOutput.can_proceed}
        requiresApproval={stageOutput.requires_approval}
        hasAlternatives={stageOutput.recommendations.some(r => r.alternatives.length > 0)}
        onApprove={() => onApprove(selectedOptions)}
        onModify={onModify}
        onBack={onBack}
        onSeeAlternatives={onSeeAlternatives}
        isLoading={isLoading}
        stageName={stageOutput.stage_title}
      />
    </div>
  );
};
