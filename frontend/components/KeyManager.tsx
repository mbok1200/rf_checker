"use client";
import { useState } from 'react';
import { clearApiKey, getApiKey, setApiKey } from '@/lib/api';

export function KeyManager() {
  const [apiKey, setKeyState] = useState<string | null>(getApiKey());

  const saveKey = (k: string) => {
    setApiKey(k);
    setKeyState(k);
  };
  const removeKey = () => {
    clearApiKey();
    setKeyState(null);
  };

  return (
    <div className="card">
      <h3>API ключ</h3>
      <div className="row">
        <input
          type="text"
          placeholder="Вставте ваш API ключ"
          defaultValue={apiKey ?? ''}
          onChange={(e) => saveKey(e.target.value)}
        />
        <button onClick={removeKey}>Видалити ключ</button>
      </div>
      <p className="hint">API ключ використовується в X-API-Key для захищених запитів.</p>
    </div>
  );
}
