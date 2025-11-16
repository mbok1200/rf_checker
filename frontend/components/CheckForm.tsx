"use client";
import { useState } from 'react';
import { api } from '@/lib/api';

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
    <div className="card">
      <h3>Перевірка контенту</h3>
      <textarea placeholder="URL по одному на рядок" rows={6} value={urlsText} onChange={e => setUrlsText(e.target.value)} />
      <input placeholder="Назва гри (Steam, опціонально)" value={gameName} onChange={e => setGameName(e.target.value)} />
      <button disabled={loading} onClick={submit}>Перевірити</button>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="result">
          <h4>Результат</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
