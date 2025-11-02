import { useState } from 'react';
import { MessageCircleQuestion, Lightbulb, CheckCircle, Send } from 'lucide-react';

interface ClarificationQuestion {
  question: string;
  rationale: string;
  options?: string[];
  category?: string;
}

interface ClarificationViewProps {
  questions: ClarificationQuestion[];
  chainOfThought?: string;
  decisionsMade?: string[];
  currentUnderstanding?: string;
  ambiguities?: string[];
  onSubmit: (answers: Record<string, string>) => void;
  isSubmitting: boolean;
}

export default function ClarificationView({
  questions,
  chainOfThought,
  decisionsMade = [],
  currentUnderstanding,
  ambiguities = [],
  onSubmit,
  isSubmitting,
}: ClarificationViewProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleAnswerChange = (question: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [question]: answer,
    }));
  };

  const handleSubmit = () => {
    // Validate all questions are answered
    const unanswered = questions.filter(q => !answers[q.question] || !answers[q.question].trim());
    
    if (unanswered.length > 0) {
      alert(`Please answer all questions. Missing: ${unanswered.length} question(s)`);
      return;
    }

    onSubmit(answers);
  };

  const allAnswered = questions.every(q => answers[q.question]?.trim());

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <MessageCircleQuestion className="w-8 h-8 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h2 className="text-2xl font-bold text-blue-900 mb-2">
              Clarification Needed
            </h2>
            <p className="text-blue-700">
              The Requirements Agent needs more information to design the optimal architecture.
              Please answer the following questions to continue.
            </p>
          </div>
        </div>
      </div>

      {/* Chain of Thought Section */}
      {chainOfThought && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <Lightbulb className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">
                Agent's Reasoning Process
              </h3>
              <div className="text-purple-800 text-sm whitespace-pre-wrap leading-relaxed">
                {chainOfThought}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Current Understanding */}
      {currentUnderstanding && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-5">
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-green-900 mb-2">
                Current Understanding
              </h3>
              <p className="text-green-800 text-sm leading-relaxed">
                {currentUnderstanding}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Decisions Made */}
      {decisionsMade && decisionsMade.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-amber-900 mb-3">
            Decisions Made So Far
          </h3>
          <ul className="space-y-2">
            {decisionsMade.map((decision, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span className="text-amber-800 text-sm">{decision}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Ambiguities Detected */}
      {ambiguities && ambiguities.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3">
            Ambiguities Detected
          </h3>
          <ul className="space-y-2">
            {ambiguities.map((ambiguity, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-yellow-600 mt-1">⚠️</span>
                <span className="text-yellow-800 text-sm">{ambiguity}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clarification Questions */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900">
            Please Answer These Questions
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {questions.length} question{questions.length !== 1 ? 's' : ''} • All fields required
          </p>
        </div>

        <div className="p-6 space-y-6">
          {questions.map((q, idx) => (
            <div key={idx} className="space-y-3 pb-6 border-b border-gray-200 last:border-b-0 last:pb-0">
              {/* Question Category */}
              {q.category && (
                <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded">
                  {q.category}
                </span>
              )}

              {/* Question Text */}
              <div className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center mt-0.5">
                  {idx + 1}
                </span>
                <p className="text-lg font-semibold text-gray-900 flex-1">
                  {q.question}
                </p>
              </div>

              {/* Rationale */}
              <div className="ml-8 bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-700 italic">
                  <strong>Why this matters:</strong> {q.rationale}
                </p>
              </div>

              {/* Answer Input */}
              <div className="ml-8">
                {q.options && q.options.length > 0 ? (
                  // Radio buttons for predefined options
                  <div className="space-y-2">
                    {q.options.map((option, optIdx) => (
                      <label
                        key={optIdx}
                        className="flex items-center space-x-3 p-3 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer transition"
                      >
                        <input
                          type="radio"
                          name={`question-${idx}`}
                          value={option}
                          checked={answers[q.question] === option}
                          onChange={() => handleAnswerChange(q.question, option)}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-gray-800">{option}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  // Text area for open-ended questions
                  <textarea
                    value={answers[q.question] || ''}
                    onChange={(e) => handleAnswerChange(q.question, e.target.value)}
                    placeholder="Enter your answer here..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={3}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-center pt-4">
        <button
          onClick={handleSubmit}
          disabled={!allAnswered || isSubmitting}
          className={`
            px-8 py-4 rounded-lg font-semibold text-lg flex items-center space-x-3 transition-all
            ${
              allAnswered && !isSubmitting
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          <Send className="w-5 h-5" />
          <span>
            {isSubmitting
              ? 'Processing Your Answers...'
              : allAnswered
              ? 'Continue with Architecture Design'
              : `Answer All Questions to Continue (${questions.filter(q => answers[q.question]?.trim()).length}/${questions.length})`}
          </span>
        </button>
      </div>

      {/* Progress Indicator */}
      <div className="text-center text-sm text-gray-500">
        <p>
          Progress: Requirements Analysis → <strong className="text-blue-600">Clarification</strong> → Architecture Design → Cost Estimation → Documentation
        </p>
      </div>
    </div>
  );
}
