const DEFAULT_API_URL = 'http://localhost:8000';

// Tabs
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const tabName = tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
  });
});

// Load settings
chrome.storage.sync.get(['apiUrl', 'apiKey'], (data) => {
  document.getElementById('api-url').value = data.apiUrl || DEFAULT_API_URL;
  if (data.apiKey) {
    document.getElementById('api-key').value = data.apiKey;
  }
});

// Load last check result
chrome.storage.local.get(['lastCheck'], (data) => {
  if (data.lastCheck) {
    displayResult(data.lastCheck.result);
  }
});

// Load selected text from storage
chrome.storage.local.get(['selectedText'], (data) => {
  if (data.selectedText) {
    const gameInput = document.getElementById('game-name');
    if (gameInput) {
      gameInput.value = data.selectedText;
      gameInput.placeholder = 'Виділений текст: ' + data.selectedText.substring(0, 30) + '...';
    }
  }
});

// Save settings
document.getElementById('save-settings').addEventListener('click', () => {
  const apiUrl = document.getElementById('api-url').value.trim();
  const apiKey = document.getElementById('api-key').value.trim();
  
  chrome.storage.sync.set({ apiUrl, apiKey }, () => {
    const status = document.getElementById('settings-status');
    status.className = 'status success';
    status.textContent = '✅ Налаштування збережено';
    setTimeout(() => status.textContent = '', 2000);
  });
});

// Get current tab URL and selected text
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]) {
    document.getElementById('current-url').value = tabs[0].url;
    
    // Try to get selected text from active tab
    chrome.tabs.sendMessage(tabs[0].id, { action: 'getSelectedText' }, (response) => {
      if (response && response.text) {
        const gameInput = document.getElementById('game-name');
        if (gameInput && !gameInput.value) {
          gameInput.value = response.text;
        }
      }
    });
  }
});

// Check button
document.getElementById('check-btn').addEventListener('click', async () => {
  const btn = document.getElementById('check-btn');
  const resultDiv = document.getElementById('result');
  
  btn.disabled = true;
  btn.textContent = 'Перевірка...';
  resultDiv.className = 'status loading';
  resultDiv.textContent = 'Аналіз контенту...';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;
    const gameName = document.getElementById('game-name').value.trim();

    const { apiUrl, apiKey } = await chrome.storage.sync.get(['apiUrl', 'apiKey']);
    
    if (!apiKey) {
      throw new Error('Будь ласка, встановіть API ключ у налаштуваннях');
    }

    // Build payload with both urls and game_name
    const payload = {
      urls: [url]
    };
    
    if (gameName) {
      payload.game_name = gameName;
    }

    const response = await fetch(`${apiUrl || DEFAULT_API_URL}/api/check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Помилка API');
    }

    const data = await response.json();
    
    // Parse message
    let analysis;
    try {
      analysis = JSON.parse(data.message);
    } catch {
      analysis = { text: data.message, is_russian_content: null };
    }

    // Save and display result
    chrome.storage.local.set({
      lastCheck: {
        url: url,
        gameName: gameName,
        result: analysis,
        timestamp: new Date().toISOString()
      }
    });
    
    displayResult(analysis);

  } catch (error) {
    resultDiv.className = 'status error';
    resultDiv.textContent = `❌ ${error.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Перевірити сторінку';
  }
});

// Helper function to display result
function displayResult(analysis) {
  const resultDiv = document.getElementById('result');
  resultDiv.className = `result ${analysis.is_russian_content ? 'danger' : 'safe'}`;
  resultDiv.innerHTML = `
    <h4>${analysis.is_russian_content ? '⚠️ Виявлено російський контент' : '✅ Російський контент не виявлено'}</h4>
    <p>${analysis.text}</p>
  `;
}