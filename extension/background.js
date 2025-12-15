const DEFAULT_API_URL = 'https://ai_api.workerinua.fun';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'check-page',
    title: 'Перевірити сторінку на RF контент',
    contexts: ['page', 'link', 'selection']
  });
});

function isURL(text) { try { new URL(text); return true; } catch { return false; } }

// Check only game
async function checkGameOnly(gameName) {
  let noteId;
  try {
    noteId = await createNote('Перевірка гри: ' + gameName.substring(0, 30) + '...');
    const { apiUrl, apiKey, userId } = await chrome.storage.sync.get(['apiUrl','apiKey','userId']);
    if (!apiKey || !userId) throw new Error('Будь ласка, увійдіть у налаштуваннях');

    const payload = { game_name: gameName, user_id: userId };
    const resp = await fetch(`${(apiUrl || DEFAULT_API_URL).replace(/\/+$/,'')}/api/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify(payload)
    });
    await handleResponse(resp, { gameName });
  } catch (error) {
    await endNoteError(noteId, error);
  }
}

// Check URL(s) with optional game
async function checkUrl(url, gameName = null) {
  let noteId;
  try {
    noteId = await createNote('Перевірка сторінки...');
    const { apiUrl, apiKey, userId } = await chrome.storage.sync.get(['apiUrl','apiKey','userId']);
    if (!apiKey || !userId) throw new Error('Будь ласка, увійдіть у налаштуваннях');

    const payload = { urls: Array.isArray(url) ? url : [url], user_id: userId };
    if (gameName) payload.game_name = gameName;

    const resp = await fetch(`${(apiUrl || DEFAULT_API_URL).replace(/\/+$/,'')}/api/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify(payload)
    });
    await handleResponse(resp, { url, gameName });
  } catch (error) {
    await endNoteError(noteId, error);
  }
}

// Check text
async function checkText(text) {
  let noteId;
  try {
    noteId = await createNote(`Перевірка тексту (${text.length} символів)...`);
    const { apiUrl, apiKey, userId } = await chrome.storage.sync.get(['apiUrl','apiKey','userId']);
    if (!apiKey || !userId) throw new Error('Будь ласка, увійдіть у налаштуваннях');

    const payload = { text, user_id: userId };
    const resp = await fetch(`${(apiUrl || DEFAULT_API_URL).replace(/\/+$/,'')}/api/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify(payload)
    });
    await handleResponse(resp, { text: text.substring(0,100)+'...' });
  } catch (error) {
    await endNoteError(noteId, error);
  }
}

async function handleResponse(resp, meta) {
  if (!resp.ok) {
    let error = 'API error';
    try { const j = await resp.json(); error = j.detail || error; } catch {}
    throw new Error(error);
  }
  const data = await resp.json();
  let analysis;
  try { analysis = JSON.parse(data.message); } catch { analysis = { text: data.message, is_russian_content: null }; }

  // Save last result for popup
  await chrome.storage.local.set({
    lastCheck: {
      ...meta,
      result: analysis,
      raw: data.message, // optional
      timestamp: new Date().toISOString()
    }
  });

  // Notify user
  await chrome.notifications.clear('checking');
  chrome.notifications.create('result', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: analysis.is_russian_content ? '⚠️ Виявлено RF контент' : '✅ Контент безпечний',
    message: analysis.text.substring(0, 200) + (analysis.text.length > 200 ? '...' : ''),
    priority: 2,
    requireInteraction: true
  });
}

async function createNote(message) {
  chrome.notifications.create('checking', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'RF Checker',
    message
  });
  return 'checking';
}
async function endNoteError(noteId, error) {
  if (noteId) await chrome.notifications.clear(noteId);
  chrome.notifications.create('error', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'RF Checker - Помилка',
    message: error.message || 'Не вдалося виконати перевірку',
    priority: 2
  });
}

// Context menu: page / link / selection
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== 'check-page') return;
  const selectedText = info.selectionText?.trim() || '';
  if (info.linkUrl) {
    // Якщо клік по лінку — перевіряємо URL
    checkUrl(info.linkUrl, null);
  } else if (selectedText) {
    if (isURL(selectedText)) checkUrl(selectedText, null);
    else if (selectedText.length <= 100) checkGameOnly(selectedText);
    else checkText(selectedText);
  } else {
    const urlToCheck = info.linkUrl || info.pageUrl || tab.url;
    checkUrl(urlToCheck, null);
  }
});

// Popup/background bridge
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  const run = async () => {
    if (request.action === 'checkUrl') await checkUrl(request.urls || request.url, request.gameName);
    else if (request.action === 'checkGameOnly') await checkGameOnly(request.game_name || request.gameName);
    else if (request.action === 'checkText') await checkText(request.text);
  };
  run().then(() => sendResponse({ success: true }))
    .catch(e => sendResponse({ success: false, error: e.message }));
  return true;
});