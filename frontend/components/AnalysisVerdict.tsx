interface AnalysisVerdictProps {
  isRussian: boolean | null;
  text: string;
}

export function AnalysisVerdict({ isRussian, text }: AnalysisVerdictProps) {
  return (
    <div className={`verdict ${isRussian ? 'danger' : isRussian === false ? 'safe' : ''}`}>
      <h4>
        {isRussian === true && '⚠️ Виявлено російський контент'}
        {isRussian === false && '✅ Російський контент не виявлено'}
        {isRussian === null && 'ℹ️ Результат аналізу'}
      </h4>
      <p>{text}</p>

      <style jsx>{`
        .verdict {
          padding: 1.5rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }
        .verdict.safe {
          background: #7c7c7cff;
          border-left: 4px solid #4caf50;
        }
        .verdict.danger {
          background: #afafafff;
          border-left: 4px solid #f44336;
        }
        .verdict h4 {
          margin: 0 0 0.5rem 0;
        }
        .verdict p {
          margin: 0;
          line-height: 1.6;
        }
      `}</style>
    </div>
  );
}