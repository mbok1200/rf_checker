"use client";
import { useState } from 'react';
import { api, setApiKey } from '@/lib/api';

export function RegisterForm() {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [loading, setL] = useState(false);
  const [error, setE] = useState<string | null>(null);
  const [issuedKey, setIssuedKey] = useState<string | null>(null);

  const submit = async () => {
    setE(null); setL(true);
    try {
      const res = await api.register(username, password);
      setIssuedKey(res.api_key);
      setApiKey(res.api_key);
    } catch (e: any) {
      setE(e.message || 'Error');
    } finally {
      setL(false);
    }
  };

  return (
    <div className="card">
      <h3>Реєстрація</h3>
      <input placeholder="username" value={username} onChange={e => setU(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e => setP(e.target.value)} />
      <button disabled={loading} onClick={submit}>Зареєструвати</button>
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

export function LoginForm() {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [loading, setL] = useState(false);
  const [error, setE] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);

  const login = async () => {
    setE(null); setL(true);
    try {
      const res = await api.login(username, password);
      setApiKey(res.api_key);

    } catch (e: any) {
      setE(e.message || 'Error');
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
      <input placeholder="username" value={username} onChange={e => setU(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e => setP(e.target.value)} />
      <div className="row">
        <button disabled={loading} onClick={login}>Увійти</button>
        <button disabled={loading} onClick={regenerate}>Згенерувати новий API ключ</button>
      </div>
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
