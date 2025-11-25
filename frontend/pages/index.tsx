import { useEffect, useState } from 'react';
import type { NextPage } from 'next';
import { api, getApiKey } from '@/lib/api';
import { KeyManager } from '@/components/KeyManager';
import { RegisterForm, LoginForm } from '@/components/AuthForms';
import { CheckForm } from '@/components/CheckForm';

const Home: NextPage = () => {
  const [tab, setTab] = useState<'check' | 'login' | 'register' | 'settings'>('check');
  const [health, setHealth] = useState<string>('...');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  useEffect(() => {
    const apiKey = getApiKey();
    setIsAuthenticated(!!apiKey);

    api.health().then(h => setHealth(`${h.status} @ ${h.timestamp}`)).catch(() => setHealth('down'));
  }, []);

  return (
    <div className="container">
      <nav className="nav">
        <button className={tab === 'check' ? 'active' : ''} onClick={() => setTab('check')}>Перевірка</button>
        
        {!isAuthenticated && (
          <>
            <button className={tab === 'login' ? 'active' : ''} onClick={() => setTab('login')}>Логін</button>
            <button className={tab === 'register' ? 'active' : ''} onClick={() => setTab('register')}>Реєстрація</button>
          </>
        )}

        {isAuthenticated && (
          <button className={tab === 'settings' ? 'active' : ''} onClick={() => setTab('settings')}>Налаштування</button>
        )}
        </nav>

      <div className="status">Backend: {health}</div>

      {tab === 'check' && <CheckForm />}
      {tab === 'login' && <LoginForm />}
      {tab === 'register' && <RegisterForm />}
      {tab === 'settings' && <KeyManager />}
    </div>
  );
};

export default Home;
