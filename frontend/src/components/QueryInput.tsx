import React from 'react';

interface QueryInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  'Describe the land cover and major objects visible in this image.',
  'Identify all water bodies and estimate coverage.',
  'What changed between these two images?',
  'Use optical and SAR to identify built-up areas.',
  'Where is the reservoir located in this image?',
];

export const QueryInput: React.FC<QueryInputProps> = ({ value, onChange, disabled }) => {
  return (
    <div>
      <div className="query-input-wrap">
        <textarea
          className="query-input"
          placeholder="Ask a question about the remote sensing imagery (e.g. 'Describe land cover', 'What changed?')..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        />
      </div>

      <div className="query-chips">
        {SUGGESTIONS.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            className="query-chip"
            onClick={() => onChange(chip)}
            disabled={disabled}
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
};
