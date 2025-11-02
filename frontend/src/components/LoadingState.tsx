import React from 'react';
import { Loader2, Brain, Search, MessageSquare } from 'lucide-react';
import './LoadingState.css';

export type LoadingType = 
  | 'generating_questions'  // Round 1: Generating initial questions
  | 'analyzing_answers'     // Between rounds: Analyzing answers
  | 'generating_followups'  // Round 2+: Generating follow-up questions
  | 'generating_architecture' // Stage 2+: Generating architecture
  | 'default';              // Generic loading

interface LoadingStateProps {
  type?: LoadingType;
  round?: number;
  message?: string;
}

const loadingConfig: Record<LoadingType, {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  estimatedTime?: string;
}> = {
  generating_questions: {
    icon: <MessageSquare className="loading-icon" />,
    title: "Generating Questions",
    subtitle: "AI is analyzing your requirements and generating contextual questions...",
    estimatedTime: "~15 seconds"
  },
  analyzing_answers: {
    icon: <Brain className="loading-icon brain-pulse" />,
    title: "Analyzing Your Answers",
    subtitle: "AI is determining if additional information is needed...",
    estimatedTime: "~5 seconds"
  },
  generating_followups: {
    icon: <Search className="loading-icon" />,
    title: "Generating Follow-Up Questions",
    subtitle: "AI is creating targeted questions based on your previous answers...",
    estimatedTime: "~10 seconds"
  },
  generating_architecture: {
    icon: <Loader2 className="loading-icon spin" />,
    title: "Generating Architecture",
    subtitle: "AI is designing your cloud solution...",
    estimatedTime: "~8 seconds"
  },
  default: {
    icon: <Loader2 className="loading-icon spin" />,
    title: "Processing",
    subtitle: "Please wait...",
  }
};

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  type = 'default', 
  round,
  message 
}) => {
  const config = loadingConfig[type];
  
  // Customize title for follow-ups with round number
  let title = config.title;
  if (type === 'generating_followups' && round) {
    title = `Generating Round ${round} Questions`;
  }
  if (type === 'generating_questions' && round) {
    title = `Generating Round ${round} Questions`;
  }

  return (
    <div className="loading-state">
      <div className="loading-content">
        <div className="loading-icon-container">
          {config.icon}
        </div>
        
        <h3 className="loading-title">{title}</h3>
        
        <p className="loading-subtitle">
          {message || config.subtitle}
        </p>
        
        {config.estimatedTime && (
          <div className="loading-time">
            <span className="time-badge">{config.estimatedTime}</span>
          </div>
        )}
        
        <div className="loading-bar">
          <div className="loading-bar-progress"></div>
        </div>
        
        {type === 'generating_questions' && (
          <div className="loading-details">
            <p className="detail-text">
              🔍 <strong>Phase 1:</strong> Detecting services and patterns<br/>
              🔍 <strong>Phase 2:</strong> Analyzing context level<br/>
              🧠 <strong>Phase 3:</strong> Generating contextual questions
            </p>
          </div>
        )}
        
        {type === 'analyzing_answers' && (
          <div className="loading-details">
            <p className="detail-text">
              ✅ Reviewing your answers<br/>
              📊 Identifying gaps in requirements<br/>
              🤔 Deciding if more questions needed
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
