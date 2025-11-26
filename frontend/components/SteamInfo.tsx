interface SteamInfoProps {
  info: {
    name: string;
    header_image?: string;
    developers?: string[];
    publishers?: string[];
    release_date?: string;
    price?: string;
    short_description?: string;
  };
}

export function SteamInfo({ info }: SteamInfoProps) {
  return (
    <div className="steam-info">
      <h4>🎮 Інформація про гру</h4>
      <div className="game-header">
        {info.header_image && (
          <img src={info.header_image} alt={info.name} />
        )}
        <div className="game-details">
          <h5>{info.name}</h5>
          {info.developers && (
            <p><strong>Розробник:</strong> {info.developers.join(', ')}</p>
          )}
          {info.publishers && (
            <p><strong>Видавець:</strong> {info.publishers.join(', ')}</p>
          )}
          {info.release_date && (
            <p><strong>Дата випуску:</strong> {info.release_date}</p>
          )}
          {info.price && (
            <p><strong>Ціна:</strong> {info.price}</p>
          )}
        </div>
      </div>
      {info.short_description && (
        <p className="description">{info.short_description}</p>
      )}

      <style jsx>{`
        .steam-info {
          background: #a3a3a3ff;
          padding: 1.5rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }
        .steam-info h4 {
          margin: 0 0 1rem 0;
        }
        .game-header {
          color: #666;
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        .game-header img {
          color: #666;
          width: 300px;
          height: auto;
          border-radius: 4px;
        }
        .game-details h5 {
          color: #666;
          margin: 0 0 0.5rem 0;
          font-size: 1.5rem;
        }
        .game-details p {
          color: #666;
          margin: 0.25rem 0;
        }
        .description {
          margin-top: 1rem;
          line-height: 1.6;
          color: #666;
        }
      `}</style>
    </div>
  );
}