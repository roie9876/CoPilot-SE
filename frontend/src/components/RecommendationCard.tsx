import React, { useState } from 'react';
import './RecommendationCard.css';

interface TradeOff {
  option_name: string;
  pros: string[];
  cons: string[];
  cost_impact: string;
  performance_impact?: string;
  recommended: boolean;
}

interface Recommendation {
  decision_name: string;
  recommendation: string;
  reasoning: string;
  trade_offs: TradeOff[];
  alternatives: string[];
  cost_impact: string;
  dependencies?: string[];
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  onShowAlternatives?: () => void;
  onModify?: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onShowAlternatives,
  onModify,
}) => {
  const [showReasoning, setShowReasoning] = useState(true);
  const [showTradeoffs, setShowTradeoffs] = useState(true);

  return (
    <div className="recommendation-card">
      <div className="recommendation-header">
        <h3 className="recommendation-title">{recommendation.decision_name}</h3>
        <div className="recommendation-cost-badge">{recommendation.cost_impact}</div>
      </div>

      <div className="recommendation-choice">
        <div className="recommendation-icon">🎯</div>
        <div className="recommendation-text">
          <div className="recommendation-label">AI Recommendation</div>
          <div className="recommendation-value">{recommendation.recommendation}</div>
        </div>
      </div>

      {/* Reasoning Section */}
      <div className="recommendation-section">
        <button
          className="section-toggle"
          onClick={() => setShowReasoning(!showReasoning)}
        >
          <span className="section-icon">💡</span>
          <span className="section-title">Why This Recommendation?</span>
          <span className={`toggle-arrow ${showReasoning ? 'open' : ''}`}>▼</span>
        </button>
        {showReasoning && (
          <div className="section-content">
            <p className="reasoning-text">{recommendation.reasoning}</p>
          </div>
        )}
      </div>

      {/* Trade-offs Section */}
      {recommendation.trade_offs && recommendation.trade_offs.length > 0 && (
        <div className="recommendation-section">
          <button
            className="section-toggle"
            onClick={() => setShowTradeoffs(!showTradeoffs)}
          >
            <span className="section-icon">⚖️</span>
            <span className="section-title">Trade-off Analysis</span>
            <span className={`toggle-arrow ${showTradeoffs ? 'open' : ''}`}>▼</span>
          </button>
          {showTradeoffs && (
            <div className="section-content">
              <div className="tradeoffs-grid">
                {recommendation.trade_offs.map((tradeoff, index) => (
                  <div
                    key={index}
                    className={`tradeoff-card ${tradeoff.recommended ? 'recommended' : ''}`}
                  >
                    <div className="tradeoff-header">
                      <h4 className="tradeoff-name">{tradeoff.option_name}</h4>
                      {tradeoff.recommended && (
                        <span className="recommended-badge">Recommended</span>
                      )}
                    </div>

                    <div className="tradeoff-details">
                      <div className="tradeoff-metric">
                        <span className="metric-label">Cost:</span>
                        <span className="metric-value">{tradeoff.cost_impact}</span>
                      </div>
                      {tradeoff.performance_impact && (
                        <div className="tradeoff-metric">
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
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Alternatives Section */}
      {recommendation.alternatives && recommendation.alternatives.length > 0 && (
        <div className="alternatives-section">
          <div className="alternatives-header">
            <span className="section-icon">🔄</span>
            <span className="section-title">Other Options</span>
          </div>
          <div className="alternatives-list">
            {recommendation.alternatives.map((alt, index) => (
              <div key={index} className="alternative-item">
                {alt}
              </div>
            ))}
          </div>
          {onShowAlternatives && (
            <button className="alternatives-button" onClick={onShowAlternatives}>
              See Detailed Comparison
            </button>
          )}
        </div>
      )}

      {/* Dependencies */}
      {recommendation.dependencies && recommendation.dependencies.length > 0 && (
        <div className="dependencies-section">
          <div className="dependencies-label">Dependencies:</div>
          <div className="dependencies-list">
            {recommendation.dependencies.map((dep, index) => (
              <span key={index} className="dependency-tag">
                {dep}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action Button */}
      {onModify && (
        <div className="recommendation-actions">
          <button className="modify-button" onClick={onModify}>
            ✏️ Modify This Decision
          </button>
        </div>
      )}
    </div>
  );
};
