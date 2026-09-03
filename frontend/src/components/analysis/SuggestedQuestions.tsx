import React from 'react';
import type { InputConfiguration } from '../../types';

interface SuggestedQuestionsProps {
  configuration?: InputConfiguration;
  onSelectQuestion: (question: string) => void;
  disabled?: boolean;
}

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  configuration = 'SINGLE_OPTICAL',
  onSelectQuestion,
  disabled = false,
}) => {
  let suggestions: string[] = [];

  if (configuration === 'OPTICAL_SAR_PAIR') {
    suggestions = [
      'What complementary information do these sensors provide?',
      'What does the optical image show vs what SAR reveals?',
      'Identify urban structures and water bodies across both sensors.',
    ];
  } else if (configuration === 'BI_TEMPORAL') {
    suggestions = [
      'What changed between these two images?',
      'Where is the largest built-up or vegetation change?',
      'Describe the major land-cover differences.',
    ];
  } else if (configuration === 'SINGLE_SAR') {
    suggestions = [
      'What structural features produce strong radar backscatter?',
      'Identify water bodies and smooth specular surfaces.',
      'Analyze vertical built-up density.',
    ];
  } else {
    // Single Optical (Default)
    suggestions = [
      'What is visible in this image?',
      'Where are the major buildings?',
      'Describe the land cover and major objects.',
      'Identify all water bodies in this scene.',
    ];
  }

  return (
    <div className="suggested-questions flex flex-col gap-1.5 mt-2">
      <div className="text-[10px] font-mono text-text-3 uppercase tracking-wider">
        SUGGESTED QUESTIONS:
      </div>

      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            disabled={disabled}
            onClick={() => onSelectQuestion(q)}
            className="text-[11px] text-left px-2.5 py-1 rounded-md bg-surface-2 hover:bg-surface-3 border border-glass-border text-text-2 hover:text-text transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            "{q}"
          </button>
        ))}
      </div>
    </div>
  );
};
