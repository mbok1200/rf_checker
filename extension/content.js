// Перевірки chrome API без доступу до undefined властивостей
const hasChrome = typeof chrome === 'object' && !!chrome && !!chrome.runtime;

let hasStorageLocal = false;
try {
  hasStorageLocal =
    typeof chrome === 'object' &&
    !!chrome &&
    !!chrome.storage &&
    !!chrome.storage.local;
} catch {
  hasStorageLocal = false;
}

const MAX_GAME_NAME_LENGTH = 500;
const MAX_TEXT_LENGTH = 2000;

// Ігрові сайти
const GAMING_SITES = [
  'store.steampowered.com',
  'store.epicgames.com',
  'www.gog.com',
  'www.origin.com',
  'www.ubisoft.com',
  'www.ea.com',
  'store.playstation.com',
  'www.xbox.com',
  'itch.io',
  'www.humblebundle.com',
  'www.greenmangaming.com'
];

function isGamingSite() {
  return GAMING_SITES.some(site => window.location.hostname.includes(site));
}

function isURL(text) {
  try {
    new URL(text);
    return true;
  } catch {
    return false;
  }
}

function isLikelyGameName(text) {
  if (!text || text.length < 2 || text.length > 100) {
    return false;
  }
  
  if (isURL(text)) {
    return false;
  }
  
  const gamePatterns = [
    /^[A-Za-z0-9\s:'\-&.!]+$/,
    /\d+/,
    /:/,
    /\b(game|edition|remastered|collection|simulator|warfare|saga|legend|chronicles)\b/i
  ];
  
  const badPatterns = [
    /^https?:\/\//,
    /\n/,
    /@|#|\$/,
    /^\d+$/,
    /^[^a-zA-Z]+$/
  ];
  
  if (badPatterns.some(pattern => pattern.test(text))) {
    return false;
  }
  
  if (gamePatterns.some(pattern => pattern.test(text))) {
    return true;
  }
  
  const words = text.trim().split(/\s+/);
  if (words.length >= 2 && words.length <= 5) {
    const hasCapitalWords = words.some(w => /^[A-Z]/.test(w));
    if (hasCapitalWords) {
      return true;
    }
  }
  
  return false;
}

let checkButton = null;
let selectedText = '';

function createCheckButton() {
  const button = document.createElement('div');
  button.id = 'rf-checker-button';
  button.innerHTML = '🛡️';
  button.style.cssText = `
    position: absolute;
    width: 32px;
    height: 32px;
    background: #0070f3;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    z-index: 999999;
    transition: transform 0.2s;
  `;
  button.addEventListener('mouseenter', () => (button.style.transform = 'scale(1.1)'));
  button.addEventListener('mouseleave', () => (button.style.transform = 'scale(1)'));
  button.addEventListener('click', () => {
    if (!hasChrome) return;
    
    const payload = {};
    
    // Якщо це назва гри — передаємо як gameName (до 500 символів)
    if (isLikelyGameName(selectedText)) {
      payload.gameName = selectedText.substring(0, MAX_GAME_NAME_LENGTH);
      payload.action = 'checkGameOnly';
    } 
    // Якщо це URL — передаємо як url
    else if (isURL(selectedText)) {
      payload.url = selectedText;
      payload.action = 'checkUrl';
    }
    // Інакше — це текст (обмежуємо до 2000 символів)
    else {
      payload.text = selectedText.substring(0, MAX_TEXT_LENGTH);
      payload.action = 'checkText';
    }
    
    chrome.runtime.sendMessage(payload);
    hideCheckButton();
  });
  return button;
}

function showCheckButton(x, y) {
  if (!checkButton) {
    checkButton = createCheckButton();
    document.body.appendChild(checkButton);
  }
  checkButton.style.left = `${x}px`;
  checkButton.style.top = `${y - 40}px`;
  checkButton.style.display = 'flex';
}

function hideCheckButton() {
  if (checkButton) checkButton.style.display = 'none';
}

document.addEventListener('mouseup', () => {
  setTimeout(() => {
    const selection = window.getSelection();
    const text = selection ? selection.toString().trim() : '';
    selectedText = text;

    // Перевірка чи є виділений текст посиланням
    let isLink = false;
    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const container = range.commonAncestorContainer;
      const parentElement = container.nodeType === 1 ? container : container.parentElement;
      isLink = parentElement && parentElement.closest('a') !== null;
    }

    // Показати кнопку тільки якщо:
    // 1. Є виділений текст
    // 2. І (це посилання АБО сайт ігровий)
    if (text && (isLink || isGamingSite())) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      showCheckButton(
        rect.left + window.scrollX + rect.width / 2 - 16,
        rect.top + window.scrollY
      );
    } else {
      hideCheckButton();
    }

    if (text && hasStorageLocal) {
      try {
        chrome.storage.local.set({ selectedText: text });
      } catch (e) {
        console.debug('content: storage set failed', e);
      }
    }
    if (text && hasChrome) {
      try {
        chrome.runtime.sendMessage({ action: 'selectedText', text }, () => {});
      } catch (e) {
        console.debug('content: sendMessage failed', e);
      }
    }
  }, 10);
});

document.addEventListener('mousedown', (e) => {
  if (e.target.id !== 'rf-checker-button') hideCheckButton();
});

if (hasChrome) {
  chrome.runtime.onMessage.addListener((req, _sender, sendResponse) => {
    if (req.action === 'getPageUrl') {
      sendResponse({ url: window.location.href });
      return true;
    }
    if (req.action === 'getSelectedText') {
      const text = selectedText || window.getSelection().toString().trim();
      sendResponse({ text });
      return true;
    }
  });
}