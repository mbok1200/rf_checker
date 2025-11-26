chrome.runtime.onInstalled.addListener(() => {
  console.log('RF Checker extension installed');
  
  // Create context menu
  chrome.contextMenus.create({
    id: 'check-page',
    title: 'Перевірити сторінку на RF контент',
    contexts: ['page', 'link', 'selection']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'check-page') {
    const urlToCheck = info.linkUrl || info.pageUrl || tab.url;
    const selectedText = info.selectionText;
    
    if (selectedText) {
      chrome.storage.local.set({ selectedText: selectedText });
    }
    
    checkUrl(urlToCheck, selectedText);
  }
});

// Функція перевірки URL
async function checkUrl(url, gameName = null) {
  try {
    // Показати notification про початок перевірки
    chrome.notifications.create('checking', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'RF Checker',
      message: 'Перевірка сторінки...'
    });

    const { apiUrl, apiKey } = await chrome.storage.sync.get(['apiUrl', 'apiKey']);
    
    if (!apiKey) {
      chrome.notifications.create('no-key', {
        type: 'basic',
        iconUrl: 'icons/icon48.png',
        title: 'RF Checker',
        message: 'Будь ласка, встановіть API ключ у налаштуваннях розширення',
        priority: 2
      });
      return;
    }

    const payload = { urls: [url] };
    if (gameName) {
      payload.game_name = gameName;
    }

    const response = await fetch(`${apiUrl || 'http://localhost:8000'}/api/check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API error');
    }

    const data = await response.json();
    let analysis;
    try {
      analysis = JSON.parse(data.message);
    } catch {
      analysis = { text: data.message, is_russian_content: null };
    }

    // Закрити notification про перевірку
    chrome.notifications.clear('checking');

    // Показати результат у нотифікації
    const isRussian = analysis.is_russian_content;
    chrome.notifications.create('result', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: isRussian ? '⚠️ Виявлено RF контент' : '✅ Контент безпечний',
      message: analysis.text.substring(0, 200) + (analysis.text.length > 200 ? '...' : ''),
      priority: 2,
      requireInteraction: true
    });

    // Зберегти результат у storage для показу в popup
    chrome.storage.local.set({
      lastCheck: {
        url: url,
        gameName: gameName,
        result: analysis,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    chrome.notifications.clear('checking');
    chrome.notifications.create('error', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'RF Checker - Помилка',
      message: error.message || 'Не вдалося перевірити сторінку',
      priority: 2
    });
  }
}

// Слухач повідомлень від popup та content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkUrl') {
    checkUrl(request.url, request.gameName).then(() => {
      sendResponse({ success: true });
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true; // Async response
  }
  
  if (request.action === 'openPopup') {
    // У Manifest V3 не можна відкрити popup програмно
    // Показуємо notification замість цього
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'RF Checker',
      message: 'Натисніть на іконку розширення для перевірки',
      priority: 1
    });
    sendResponse({ success: true });
  }
  
  return true;
});