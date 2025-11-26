// Listen for text selection
document.addEventListener('mouseup', () => {
  const selectedText = window.getSelection().toString().trim();
  if (selectedText) {
    // Send selected text to background or store it
    chrome.storage.local.set({ selectedText: selectedText });
  }
});

let checkButton = null;
let selectedText = '';

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

// Перевірка чи це ігровий сайт
function isGamingSite() {
  return GAMING_SITES.some(site => window.location.hostname.includes(site));
}

// Створення кнопки перевірки
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
  
  button.addEventListener('mouseenter', () => {
    button.style.transform = 'scale(1.1)';
  });
  
  button.addEventListener('mouseleave', () => {
    button.style.transform = 'scale(1)';
  });
  
  button.addEventListener('click', () => {
    chrome.storage.local.set({ selectedText: selectedText });
    chrome.runtime.sendMessage({ action: 'openPopup' });
  });
  
  return button;
}

// Показати кнопку біля виділеного тексту
function showCheckButton(x, y) {
  if (!checkButton) {
    checkButton = createCheckButton();
    document.body.appendChild(checkButton);
  }
  
  checkButton.style.left = `${x}px`;
  checkButton.style.top = `${y - 40}px`;
  checkButton.style.display = 'flex';
}

// Сховати кнопку
function hideCheckButton() {
  if (checkButton) {
    checkButton.style.display = 'none';
  }
}

// Обробник виділення тексту
document.addEventListener('mouseup', (e) => {
  setTimeout(() => {
    const selection = window.getSelection();
    selectedText = selection.toString().trim();
    
    if (selectedText && isGamingSite()) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      // Показати кнопку біля виділеного тексту
      showCheckButton(
        rect.left + window.scrollX + (rect.width / 2) - 16,
        rect.top + window.scrollY
      );
      
      // Зберегти виділений текст
      chrome.storage.local.set({ selectedText: selectedText });
    } else {
      hideCheckButton();
    }
  }, 10);
});

// Сховати кнопку при кліку поза виділенням
document.addEventListener('mousedown', (e) => {
  if (e.target.id !== 'rf-checker-button') {
    hideCheckButton();
  }
});

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageUrl') {
    sendResponse({ url: window.location.href });
  }
  if (request.action === 'getSelectedText') {
    sendResponse({ text: selectedText });
  }
  return true;
});