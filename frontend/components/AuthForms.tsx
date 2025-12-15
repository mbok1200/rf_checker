"use client";
import { useState } from 'react';
import { api, setApiKey, setUserId } from '@/lib/api';

export const LoginForm = ({ onSuccess }: { onSuccess?: () => void }) => {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [loading, setL] = useState(false);
  const [error, setE] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setE(null); setL(true);
    try {
      const res = await api.login(username, password);
      alert(`Успішний вхід! API Key: ${res.api_key}`);
      setUserId(res.user_id);
      setApiKey(res.api_key);
      onSuccess?.();
      location.reload();
    } catch (err: any) {
      setE(err.message);
    } finally {
      setL(false);
    }
  };

  const regenerate = async () => {
    setE(null); setL(true);
    try {
      const res = await api.regenerateKey(username, password);
      setNewKey(res.api_key);
      setApiKey(res.api_key);
    } catch (e: any) {
      setE(e.message || 'Error');
    } finally {
      setL(false);
    }
  };

  return (
    <div className="card">
      <h3>Логін</h3>
      <form onSubmit={handleSubmit}>
        <input placeholder="username" value={username} onChange={e => setU(e.target.value)} />
        <input placeholder="password" type="password" value={password} onChange={e => setP(e.target.value)} />
        <div className="row">
          <button disabled={loading} type="submit">Увійти</button>
          <button disabled={loading} onClick={regenerate}>Згенерувати новий API ключ</button>
        </div>
      </form>
      {newKey && (
        <div className="success">
          Новий API ключ (збережіть):
          <pre>{newKey}</pre>
        </div>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

export const RegisterForm = ({ onSuccess }: { onSuccess?: () => void }) => {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [loading, setL] = useState(false);
  const [error, setE] = useState<string | null>(null);
  const [issuedKey, setIssuedKey] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setE(null); setL(true);
    try {
      const res = await api.register(username, password);
      alert(`Реєстрація успішна! API Key: ${res.api_key}`);
      setApiKey(res.api_key);
      localStorage.setItem('apiKey', res.api_key);
      onSuccess?.();
      location.reload();
    } catch (err: any) {
      setE(err.message);
    } finally {
      setL(false);
    }
  };

  return (
    <div className="card">
      <h3>Реєстрація</h3>
      <form onSubmit={handleSubmit}>
        <input placeholder="username" value={username} onChange={e => setU(e.target.value)} />
        <input placeholder="password" type="password" value={password} onChange={e => setP(e.target.value)} />
        <button disabled={loading} type="submit">Зареєструвати</button>
      </form>
      {error && <div className="error">{error}</div>}
      {issuedKey && (
        <div className="success">
          Новий API ключ (збережіть):
          <pre>{issuedKey}</pre>
        </div>
      )}
    </div>
  );
}
