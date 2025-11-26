"use client";
import { useState } from 'react';
import { api } from '@/lib/api';
import { AnalysisResult } from './AnalysisResult';

export function CheckForm() {
  const [urlsText, setUrlsText] = useState('');
  const [gameName, setGameName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setError(null); setLoading(true); setResult(null);
    try {
      const urls = urlsText.split('\n').map(s => s.trim()).filter(Boolean);
      const payload: any = {};
      if (urls.length) payload.urls = urls;
      if (gameName.trim()) payload.game_name = gameName.trim();
      const res = await api.check(payload);
      setResult(res);
    } catch (e: any) {
      setError(e.message || 'Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="check-form">
      <h3>Перевірка контенту</h3>
      <textarea 
        placeholder="URL по одному на рядок" 
        rows={6} 
        value={urlsText} 
        onChange={e => setUrlsText(e.target.value)} 
      />
      <input 
        placeholder="Назва гри (Steam, опціонально)" 
        value={gameName} 
        onChange={e => setGameName(e.target.value)} 
      />
      <button disabled={loading} onClick={submit}>
        {loading ? 'Перевірка...' : 'Перевірити'}
      </button>
      
      {error && <div className="error">{error}</div>}
      {result && <AnalysisResult data={result} />}
      
      <style jsx>{`
        .check-form {
          max-width: 900px;
          margin: 0 auto;
        }
        textarea, input {
          width: 100%;
          margin-bottom: 1rem;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-family: inherit;
        }
        textarea {
          font-family: monospace;
          resize: vertical;
        }
        button {
          width: 100%;
          padding: 0.75rem;
          background: #0070f3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 1rem;
        }
        button:disabled {
          background: #969494ff;
          cursor: not-allowed;
        }
        .error {
          padding: 1rem;
          background: rgba(196, 195, 195, 1);
          color: #c00;
          border-radius: 4px;
          margin-top: 1rem;
        }
      `}</style>
    </div>
  );
}
