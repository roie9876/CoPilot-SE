import React, { useState } from 'react';
import { StageProgress } from './StageProgress';
import { StageApproval } from './StageApproval';
import { LoadingState } from './LoadingState';
import type { StageOutput } from '../types';
import './Stage1View.css';

interface Stage1ViewProps {
  stageOutput: StageOutput;
  sessionId: string;
  onApprove: (answers: Record<string, string>) => void;
  isLoading: boolean;
  loadingMessage?: string;
  currentRound?: number;
}

export const Stage1View: React.FC<Stage1ViewProps> = ({
  stageOutput,
  // sessionId, // Not used yet, will be needed for back navigation
  onApprove,
  isLoading,
  loadingMessage,
  currentRound = 1,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showReasoning, setShowReasoning] = useState(false);

  const handleAnswerChange = (question: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [question]: answer,
    }));
  };

  const handleApprove = () => {
    onApprove(answers);
  };

  const allQuestionsAnswered = stageOutput.questions.every(
    (q) => answers[q.question]
  );

  // Detect if this is a follow-up round or analyzing answers
  const isAnalyzingAnswers = isLoading && loadingMessage?.includes('analyz');
  const isGeneratingFollowups = isLoading && currentRound > 1 && !isAnalyzingAnswers;
  const isGeneratingInitial = isLoading && currentRound === 1;

  // Show loading state if loading
  if (isLoading) {
    if (isAnalyzingAnswers) {
      return <LoadingState type="analyzing_answers" round={currentRound} />;
    } else if (isGeneratingFollowups) {
      return <LoadingState type="generating_followups" round={currentRound} />;
    } else if (isGeneratingInitial) {
      return <LoadingState type="generating_questions" round={currentRound} />;
    } else {
      return <LoadingState type="default" message={loadingMessage} />;
    }
  }

  return (
    <div className="stage1-view">
      <StageProgress
        currentStage="stage_1_requirements"
        stagesCompleted={[]}
      />

      {/* Round Progress Indicator */}
      {currentRound > 1 && (
        <div className="round-progress">
          <span className="round-badge">Round {currentRound}</span>
          <span className="round-label">Follow-up Questions</span>
        </div>
      )}

      <div className="stage-header">
        <h2 className="stage-title">{stageOutput.stage_title}</h2>
        <p className="stage-description">{stageOutput.stage_description}</p>
      </div>

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

      <div className="questions-section">
        {stageOutput.questions.map((question, index) => (
          <div key={index} className="question-card">
            <div className="question-header">
              <span className="question-number">{index + 1}</span>
              <div className="question-content">
                <h3 className="question-text">{question.question}</h3>
                <p className="question-rationale">
                  <span className="rationale-icon">💡</span>
                  {question.rationale}
                </p>
              </div>
            </div>

            <div className="options-grid">
              {question.options && question.options.map((option, optIndex) => (
                <button
                  key={optIndex}
                  className={`option-button ${
                    answers[question.question] === option ? 'selected' : ''
                  }`}
                  onClick={() => handleAnswerChange(question.question, option)}
                  disabled={isLoading}
                >
                  <span className="option-radio">
                    {answers[question.question] === option && '✓'}
                  </span>
                  <span className="option-text">{option}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <StageApproval
        canGoBack={false}
        canProceed={allQuestionsAnswered}
        requiresApproval={true}
        hasAlternatives={false}
        onApprove={handleApprove}
        isLoading={isLoading}
        stageName="Requirements Discovery"
      />
    </div>
  );
};
