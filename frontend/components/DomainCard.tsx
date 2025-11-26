interface DomainCardProps {
  data: {
    domain: string;
    ip?: string;
    registrant_country?: string;
    registrar?: string;
    creation_date?: string;
    russian_traces?: string[];
  };
}

export function DomainCard({ data }: DomainCardProps) {
  const isSafe = data.russian_traces?.[0]?.includes('не виявлено');

  return (
    <div className="domain-card">
      <h5>{data.domain}</h5>
      <div className="meta-grid">
        <div><strong>IP:</strong> {data.ip || 'N/A'}</div>
        <div><strong>Країна:</strong> {data.registrant_country || 'Unknown'}</div>
        <div><strong>Реєстратор:</strong> {data.registrar || 'N/A'}</div>
        <div><strong>Створено:</strong> {data.creation_date || 'N/A'}</div>
      </div>
      {data.russian_traces && data.russian_traces.length > 0 && (
        <div className={`traces ${isSafe ? 'safe' : 'warning'}`}>
          <strong>Сліди РФ:</strong> {data.russian_traces.join('; ')}
        </div>
      )}

      <style jsx>{`
        .domain-card {
          background: white;
          padding: 1rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          border: 1px solid #ddd;
        }
        .domain-card h5 {
          margin: 0 0 0.75rem 0;
          color: #0070f3;
        }
        .meta-grid {
          color: #666;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }
        .traces {
          padding: 0.5rem;
          border-radius: 4px;
          margin-top: 0.5rem;
        }
        .traces.safe {
          background: #9eff81ff;
        }
        .traces.warning {
          background: #fc6161ff;
        }
      `}</style>
    </div>
  );
}