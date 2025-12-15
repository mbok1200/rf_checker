const DEFAULT_API_URL = 'https://ai_api.workerinua.fun';

function isURL(text) {
  try { new URL(text); return true; } catch { return false; }
}
function isLikelyGameName(text) {
  if (!text || text.length < 2 || text.length > 100) return false;
  if (isURL(text)) return false;
  const gamePatterns = [/^[A-Za-z0-9\s:'\-&.!]+$/, /\d+/, /:/, /\b(game|edition|remastered|collection|simulator|warfare|saga|legend|chronicles)\b/i];
  const badPatterns = [/^https?:\/\//, /\n/, /@|#|\$/, /^\d+$/, /^[^a-zA-Z]+$/];
  if (badPatterns.some(p=>p.test(text))) return false;
  if (gamePatterns.some(p=>p.test(text))) return true;
  const words = text.trim().split(/\s+/);
  return words.length>=2 && words.length<=5 && words.some(w=>/^[A-Z]/.test(w));
}

document.addEventListener('DOMContentLoaded', () => {
  // Tabs
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const pane = document.getElementById(`${tabName}-tab`);
      if (pane) pane.classList.add('active');
    });
  });

  // Elements
  const apiUrlEl = document.getElementById('api-url');
  const apiKeyEl = document.getElementById('api-key');
  const usernameEl = document.getElementById('username');
  const passwordEl = document.getElementById('password');
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const authStatus = document.getElementById('auth-status');

  const settingsStatus = document.getElementById('settings-status');
  const saveSettingsBtn = document.getElementById('save-settings');

  const currentUrlEl = document.getElementById('current-url');
  const inputMainEl = document.getElementById('input-main');
  const checkBtn = document.getElementById('check-btn');
  const useCurrentBtn = document.getElementById('use-current');
  const resultDiv = document.getElementById('result');

  // Load settings
  chrome.storage.sync.get(['apiUrl', 'apiKey', 'userId', 'username'], (data) => {
    apiUrlEl.value = data.apiUrl || DEFAULT_API_URL;
    if (data.apiKey) apiKeyEl.value = data.apiKey;
    if (data.username) usernameEl.value = data.username;
    updateAuthStatus(data.userId, data.username);
  });

  // Load last result (optional)
  chrome.storage.local.get(['lastCheck'], (data) => {
    if (data.lastCheck?.result) displayResult(data.lastCheck.result);
  });

  // Current tab URL and try get selection through content script
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs && tabs[0];
    if (!tab) return;
    currentUrlEl.value = tab.url || '';
    const request = { action: 'getSelectedText' };
    chrome.tabs.sendMessage(tab.id, request, (response) => {
      if (chrome.runtime.lastError || !response) return;
      if (response.text && !inputMainEl.value) inputMainEl.value = response.text;
    });
  });

  // Save settings
  saveSettingsBtn.addEventListener('click', () => {
    const apiUrl = (apiUrlEl.value || '').trim();
    chrome.storage.sync.set({ apiUrl }, () => {
      if (settingsStatus) {
        settingsStatus.className = 'status success';
        settingsStatus.textContent = '✅ Налаштування збережено';
        setTimeout(() => (settingsStatus.textContent = ''), 2000);
      }
    });
  });

  // Login
  loginBtn.addEventListener('click', async () => {
    const apiUrl = (apiUrlEl.value || DEFAULT_API_URL).replace(/\/+$/, '');
    const username = usernameEl.value.trim();
    const password = passwordEl.value.trim();
    if (!username || !password) {
      setAuthStatus('❌ Введіть username та password', 'error');
      return;
    }
    setAuthStatus('⏳ Вхід...', 'loading');
    try {
      const resp = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (!resp.ok) {
        const err = await safeJson(resp);
        throw new Error(err?.detail || 'Auth error');
      }
      const data = await resp.json();
      const { user_id, api_key } = data;
      if (!user_id || !api_key) throw new Error('Некоректна відповідь сервера');
      chrome.storage.sync.set({ apiUrl, apiKey: api_key, userId: user_id, username }, () => {
        apiKeyEl.value = api_key;
        updateAuthStatus(user_id, username);
        passwordEl.value = '';
        setAuthStatus('✅ Вхід успішний', 'success');
      });
    } catch (e) {
      setAuthStatus(`❌ ${e.message}`, 'error');
    }
  });

  // Logout
  logoutBtn.addEventListener('click', () => {
    chrome.storage.sync.remove(['apiKey','userId'], () => {
      apiKeyEl.value = '';
      updateAuthStatus(null, usernameEl.value || null);
      setAuthStatus('🔒 Вийшли з акаунту', 'success');
    });
  });

  // Use current URL
  useCurrentBtn.addEventListener('click', () => {
    if (currentUrlEl.value) {
      inputMainEl.value = currentUrlEl.value;
    }
  });

  // Check button
  checkBtn.addEventListener('click', async () => {
    guardResult('⏳ Аналіз контенту...', 'loading', true);
    try {
      const { apiUrl, apiKey, userId } = await chromeStorageSync(['apiUrl','apiKey','userId']);
      if (!apiKey || !userId) {
        throw new Error('Будь ласка, увійдіть у налаштуваннях (логаут/логін)');
      }

      // Build payload by detection
      const raw = (inputMainEl.value || '').trim();
      const payload = { user_id: userId };
      if (raw.includes(',')) {
        const parts = raw.split(',').map(s => s.trim()).filter(Boolean);
        const urls = parts.filter(isURL);
        if (urls.length > 0) payload.urls = urls;
        else payload.text = raw; // якщо коми є, але URL невалідні — шлемо як текст
      } else if (isURL(raw)) {
        payload.urls = [raw];
      } else if (isLikelyGameName(raw)) {
        payload.game_name = raw;
      } else if (raw) {
        payload.text = raw;
      } else if (currentUrlEl.value && isURL(currentUrlEl.value)) {
        payload.urls = [currentUrlEl.value];
      } else {
        throw new Error('Немає даних для перевірки');
      }

      // Delegate to background (notifications + збереження історії)
      chrome.runtime.sendMessage({ action: routeByPayload(payload), ...payload }, (resp) => {
        if (chrome.runtime.lastError) {
          guardResult(`❌ ${chrome.runtime.lastError.message}`, 'error');
        } else {
          // Показати останній результат, якщо вже збережено
          chrome.storage.local.get(['lastCheck'], (data) => {
            if (data.lastCheck?.result) displayResult(data.lastCheck.result);
            else guardResult('✅ Запит відправлено, чекайте сповіщення', 'success');
          });
        }
      });
    } catch (e) {
      guardResult(`❌ ${e.message}`, 'error');
    } finally {
      checkBtn.disabled = false;
      checkBtn.textContent = 'Перевірити';
    }
  });

  function routeByPayload(p) {
    if (p.text) return 'checkText';
    if (p.game_name) return 'checkGameOnly';
    return 'checkUrl';
  }

  function guardResult(msg, kind, lock=false) {
    if (lock) { checkBtn.disabled = true; checkBtn.textContent = 'Перевірка...'; }
    resultDiv.className = `status ${kind}`;
    resultDiv.textContent = msg;
  }
  function displayResult(analysisRaw) {
    let analysis = analysisRaw;

    // If backend sends stringified JSON, parse safely
    if (typeof analysisRaw === 'string') {
      try { analysis = JSON.parse(analysisRaw); }
      catch { analysis = { text: analysisRaw, is_russian_content: null }; }
    }

    // Normalize boolean flag
    const flag = typeof analysis.is_russian_content === 'boolean'
      ? analysis.is_russian_content
      : (typeof analysis.is_russian_content === 'string'
          ? analysis.is_russian_content.trim().toLowerCase() === 'true'
          : !!analysis.is_russian_content);

    const title = flag ? '⚠️ Виявлено російський контент' : '✅ Російський контент не виявлено';

    // Prefer analysis.text; if missing, pretty-print the whole object
    let body = '';
    if (typeof analysis.text === 'string' && analysis.text.length > 0) {
      body = analysis.text;
    } else {
      try { body = JSON.stringify(analysis, null, 2); }
      catch { body = String(analysis); }
    }

    // Render full content in a scrollable <pre> without truncation
    resultDiv.className = `result ${flag ? 'danger' : 'safe'}`;
    resultDiv.innerHTML = `
      <h4>${title}</h4>
      <pre style="white-space:pre-wrap;word-wrap:break-word;margin:0;max-height:280px;overflow:auto">${body}</pre>
    `;
  }
  function setAuthStatus(msg, cls) {
    authStatus.className = `status ${cls || ''}`;
    authStatus.textContent = msg || '';
  }
  function updateAuthStatus(userId, username) {
    if (userId) authStatus.textContent = `🔑 Авторизовано як ${username || 'user'} (user_id: ${userId})`;
    else authStatus.textContent = '🔒 Не авторизовано';
  }
  function safeJson(resp) { return resp.json().catch(()=>null); }
  function chromeStorageSync(keys) {
    return new Promise(resolve => chrome.storage.sync.get(keys, resolve));
  }
});