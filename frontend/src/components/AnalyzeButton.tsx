import React from 'react';

interface AnalyzeButtonProps {
  onClick: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export const AnalyzeButton: React.FC<AnalyzeButtonProps> = ({ onClick, isLoading, disabled }) => {
  return (
    <button
      type="button"
      className="analyze-btn"
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? (
        <>
          <div className="spinner" />
          <span>Orchestrating Analysis...</span>
        </>
      ) : (
        <>
          <span>⚡ Run Satellite Analysis</span>
        </>
      )}
    </button>
  );
};
