import { DomainCard } from './DomainCard';

interface UrlsMetadataProps {
  urls: any[];
}

export function UrlsMetadata({ urls }: UrlsMetadataProps) {
  return (
    <div className="urls-metadata">
      <h4>🔍 Аналіз доменів</h4>
      {urls.map((meta, idx) => (
        <DomainCard key={idx} data={meta} />
      ))}

      <style jsx>{`
        .urls-metadata h4 {
          margin-bottom: 1rem;
        }
      `}</style>
    </div>
  );
}