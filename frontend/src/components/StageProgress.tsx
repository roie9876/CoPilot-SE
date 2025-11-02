import React from 'react';
import './StageProgress.css';

interface StageProgressProps {
  currentStage: string;
  stagesCompleted: string[];
}

const STAGES = [
  { id: 'stage_1_requirements', number: 1, label: 'Requirements' },
  { id: 'stage_2_compute', number: 2, label: 'Compute' },
  { id: 'stage_3_data', number: 3, label: 'Data' },
  { id: 'stage_4_security', number: 4, label: 'Security' },
  { id: 'stage_5_review', number: 5, label: 'Review' },
];

export const StageProgress: React.FC<StageProgressProps> = ({
  currentStage,
  stagesCompleted,
}) => {
  const getStageStatus = (stageId: string): 'completed' | 'current' | 'upcoming' => {
    if (stagesCompleted.includes(stageId)) {
      return 'completed';
    }
    if (stageId === currentStage) {
      return 'current';
    }
    return 'upcoming';
  };

  return (
    <div className="stage-progress">
      <div className="stage-progress-title">Solution Design Progress</div>
      <div className="stage-progress-bar">
        {STAGES.map((stage, index) => {
          const status = getStageStatus(stage.id);
          return (
            <React.Fragment key={stage.id}>
              <div className={`stage-item stage-${status}`}>
                <div className="stage-circle">
                  {status === 'completed' ? (
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"
                        fill="white"
                      />
                    </svg>
                  ) : (
                    <span className="stage-number">{stage.number}</span>
                  )}
                </div>
                <div className="stage-label">{stage.label}</div>
              </div>
              {index < STAGES.length - 1 && (
                <div className={`stage-connector stage-connector-${status}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
