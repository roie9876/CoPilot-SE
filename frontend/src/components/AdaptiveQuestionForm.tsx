import React, { useState, useEffect } from 'react';
import { Send, AlertCircle, HelpCircle, Sparkles } from 'lucide-react';
import type { KGQuestion } from '../types-kg';
import { DOMAIN_NAMES } from '../types-kg';
import { kgAutofill } from '../api/kg-client';

const DEFAULT_NA_OPTION = 'Not applicable / not relevant';

const optionsWithNotApplicable = (options: string[]): string[] => {
  const normalized = options.map((opt) => opt.trim().toLowerCase());
  const hasExistingNA = normalized.some((opt) =>
    opt.includes('not applicable') || opt.includes('not relevant') || opt === 'none' || opt === 'n/a'
  );

  return hasExistingNA ? options : [...options, DEFAULT_NA_OPTION];
};

interface AdaptiveQuestionFormProps {
  domain: string;
  questions: KGQuestion[];
  onSubmit: (answers: Record<string, string | number | boolean | string[]>) => void;
  isSubmitting: boolean;
  sessionId: string;
}

const AdaptiveQuestionForm: React.FC<AdaptiveQuestionFormProps> = ({
  domain,
  questions,
  onSubmit,
  isSubmitting,
  sessionId,
}) => {
  const [answers, setAnswers] = useState<Record<string, string | number | boolean | string[]>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showHelp, setShowHelp] = useState<Record<string, boolean>>({});
  const [isAutoFilling, setIsAutoFilling] = useState(false);

  // Reset form when domain changes
  useEffect(() => {
    setAnswers({});
    setErrors({});
    setShowHelp({});
  }, [domain]);

  const handleInputChange = (fieldName: string, value: string | number | boolean | string[]) => {
    setAnswers((prev) => ({ ...prev, [fieldName]: value }));
    // Clear error when user starts typing
    if (errors[fieldName]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    questions.forEach((q) => {
      if (q.priority === 'critical' && !answers[q.field_name]) {
        newErrors[q.field_name] = 'This field is required';
      }

      if (answers[q.field_name] && q.validation) {
        const value = answers[q.field_name];

        if (q.validation.type === 'number') {
          const num = Number(value);
          if (isNaN(num)) {
            newErrors[q.field_name] = 'Must be a number';
          } else if (q.validation.min !== undefined && num < q.validation.min) {
            newErrors[q.field_name] = `Must be at least ${q.validation.min}`;
          } else if (q.validation.max !== undefined && num > q.validation.max) {
            newErrors[q.field_name] = `Must be at most ${q.validation.max}`;
          }
        }

        if (q.validation.type === 'string' && q.validation.pattern) {
          const pattern = new RegExp(q.validation.pattern);
          if (!pattern.test(String(value))) {
            newErrors[q.field_name] = 'Invalid format';
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(answers);
    }
  };

  const handleAutoFill = async () => {
    setIsAutoFilling(true);
    try {
      const result = await kgAutofill(sessionId, domain, questions);
      
      // Populate form with AI suggestions
      const newAnswers: Record<string, string | number | boolean | string[]> = {};
      Object.entries(result.suggested_answers).forEach(([fieldName, value]) => {
        newAnswers[fieldName] = value;
      });
      
      setAnswers(newAnswers);
      setErrors({}); // Clear any validation errors
    } catch (error) {
      console.error('Auto-fill failed:', error);
      alert('Failed to auto-fill questions. Please try again or fill manually.');
    } finally {
      setIsAutoFilling(false);
    }
  };

  const toggleHelp = (fieldName: string) => {
    setShowHelp((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }));
  };

  const renderQuestionInput = (question: KGQuestion) => {
    const value = answers[question.field_name] ?? '';

    if (question.options) {
      const selectOptions = optionsWithNotApplicable(question.options);
      // Dropdown/Select
      return (
        <select
          id={question.field_name}
          value={String(value)}
          onChange={(e) => handleInputChange(question.field_name, e.target.value)}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white cursor-pointer ${
            errors[question.field_name] ? 'border-red-500' : 'border-gray-300'
          }`}
          style={{ position: 'relative', zIndex: 10 }}
          disabled={isSubmitting || isAutoFilling}
        >
          <option value="">-- Select an option --</option>
          {selectOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );
    }

    if (question.validation?.type === 'number') {
      // Number input
      return (
        <input
          type="number"
          id={question.field_name}
          value={String(value)}
          onChange={(e) => handleInputChange(question.field_name, Number(e.target.value))}
          min={question.validation.min}
          max={question.validation.max}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            errors[question.field_name] ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={isSubmitting}
          placeholder={question.context || 'Enter a number'}
        />
      );
    }

    if (question.validation?.type === 'boolean') {
      // Checkbox
      return (
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id={question.field_name}
            checked={Boolean(value)}
            onChange={(e) => handleInputChange(question.field_name, e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          />
          <label htmlFor={question.field_name} className="text-sm text-gray-700">
            {question.context || 'Yes/No'}
          </label>
        </div>
      );
    }

    // Default: Text input
    return (
      <input
        type="text"
        id={question.field_name}
        value={String(value)}
        onChange={(e) => handleInputChange(question.field_name, e.target.value)}
        className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
          errors[question.field_name] ? 'border-red-500' : 'border-gray-300'
        }`}
        disabled={isSubmitting}
        placeholder={question.context || 'Enter your answer'}
      />
    );
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'critical':
        return (
          <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
            Required
          </span>
        );
      case 'important':
        return (
          <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
            Important
          </span>
        );
      case 'optional':
        return (
          <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
            Optional
          </span>
        );
      default:
        return null;
    }
  };

  // Get domain display name
  const domainKey = domain.replace(/_access|_platform|_connectivity|_persistence|_dr|_governance/, '');
  const domainDisplayName = DOMAIN_NAMES[domainKey as keyof typeof DOMAIN_NAMES] || domain;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-gray-800">
            {domainDisplayName} Questions
          </h2>
          <button
            type="button"
            onClick={handleAutoFill}
            disabled={isAutoFilling || isSubmitting}
            className="flex items-center space-x-2 px-4 py-2 bg-linear-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
          >
            {isAutoFilling ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>AI is thinking...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Auto-Fill with AI</span>
              </>
            )}
          </button>
        </div>
        <p className="text-gray-600">
          Please answer the following questions to help us design your architecture.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.field_name} className="space-y-2">
            {/* Question Label */}
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <label
                  htmlFor={question.field_name}
                  className="block text-sm font-medium text-gray-900 mb-1"
                >
                  <span className="mr-2">{index + 1}.</span>
                  {question.question_text}
                </label>
              </div>
              <div className="flex items-center space-x-2 ml-4">
                {getPriorityBadge(question.priority)}
                {question.context && (
                  <button
                    type="button"
                    onClick={() => toggleHelp(question.field_name)}
                    className="text-blue-500 hover:text-blue-700"
                    aria-label="Toggle help"
                  >
                    <HelpCircle className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>

            {/* Help Text */}
            {showHelp[question.field_name] && question.context && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <p>{question.context}</p>
                </div>
              </div>
            )}

            {/* Input Field */}
            {renderQuestionInput(question)}

            {/* Error Message */}
            {errors[question.field_name] && (
              <p className="text-sm text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-4 h-4" />
                <span>{errors[question.field_name]}</span>
              </p>
            )}
          </div>
        ))}

        {/* Submit Button */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Answered: {Object.keys(answers).length} / {questions.length} questions
          </p>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
          >
            {isSubmitting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Continue</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AdaptiveQuestionForm;
