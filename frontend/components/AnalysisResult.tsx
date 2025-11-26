import { AnalysisVerdict } from './AnalysisVerdict';
import { SteamInfo } from './SteamInfo';
import { UrlsMetadata } from './UrlsMetadata';

interface AnalysisResultProps {
  data: {
    message: string;
    steam_info?: any;
    urls_metadata?: any[];
    request_id: string;
    timestamp: string;
  };
}

export function AnalysisResult({ data }: AnalysisResultProps) {
  const parseMessage = (msg: string) => {
    try {
      return JSON.parse(msg);
    } catch {
      return { text: msg, is_russian_content: null };
    }
  };

  const analysis = parseMessage(data.message);

  return (
    <div className="analysis-result">
      <AnalysisVerdict 
        isRussian={analysis.is_russian_content} 
        text={analysis.text} 
      />
      
      {data.steam_info && <SteamInfo info={data.steam_info} />}
      
      {data.urls_metadata && data.urls_metadata.length > 0 && (
        <UrlsMetadata urls={data.urls_metadata} />
      )}

      <div className="metadata">
        <p><strong>ID запиту:</strong> {data.request_id}</p>
        <p><strong>Час:</strong> {new Date(data.timestamp).toLocaleString('uk-UA')}</p>
      </div>

      <style jsx>{`
        .analysis-result {
          margin-top: 1.5rem;
        }
        .metadata {
          margin-top: 1.5rem;
          padding-top: 1rem;
          border-top: 1px solid #ddd;
          font-size: 0.9rem;
          color: #666;
        }
      `}</style>
    </div>
  );
}