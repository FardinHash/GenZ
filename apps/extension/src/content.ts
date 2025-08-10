const INJECTED_ATTR = 'data-genz-injected';
let lastFocused: HTMLElement | null = null;

function isEligible(el: Element): boolean {
  if (el instanceof HTMLInputElement) {
    if (el.type === 'password' || el.type === 'hidden') return false;
    return el.type === 'text' || el.type === 'search' || el.type === 'email' || el.type === 'url' || el.type === 'tel';
  }
  if (el instanceof HTMLTextAreaElement) return true;
  const contentEditable = (el as HTMLElement).isContentEditable || el.getAttribute('contenteditable') === 'true';
  return contentEditable;
}

function createButton(target: HTMLElement): HTMLButtonElement {
  const btn = document.createElement('button');
  btn.textContent = 'Compose with AI';
  btn.setAttribute('type', 'button');
  btn.style.marginLeft = '6px';
  btn.style.padding = '4px 8px';
  btn.style.fontSize = '12px';
  btn.style.cursor = 'pointer';
  btn.style.borderRadius = '6px';
  btn.style.border = '1px solid #ccc';
  btn.style.background = '#fff';

  btn.addEventListener('click', () => {
    console.debug('[genz] compose clicked');
    // For now the popup initiates the generate flow
  });

  return btn;
}

function injectForElement(el: Element) {
  if (!(el instanceof HTMLElement)) return;
  if (el.getAttribute(INJECTED_ATTR) === '1') return;
  if (!isEligible(el)) return;

  const btn = createButton(el);
  el.after(btn);
  el.setAttribute(INJECTED_ATTR, '1');

  el.addEventListener('focus', () => {
    lastFocused = el;
  });
}

function scan() {
  const candidates = document.querySelectorAll('textarea, input[type="text"], input[type="search"], input[type="email"], input[type="url"], input[type="tel"], [contenteditable="true"], [contenteditable]');
  candidates.forEach(injectForElement);
}

const observer = new MutationObserver((mutations) => {
  for (const m of mutations) {
    m.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node as Element;
        if (isEligible(el)) injectForElement(el);
        el.querySelectorAll?.('textarea, input[type="text"], input[type="search"], input[type="email"], input[type="url"], input[type="tel"], [contenteditable="true"], [contenteditable]').forEach(injectForElement);
      }
    });
  }
});

function insertTextAtTarget(target: HTMLElement, text: string) {
  if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
    const sep = target.value ? ' ' : '';
    target.value += sep + text;
    target.dispatchEvent(new Event('input', { bubbles: true }));
    return;
  }
  if ((target as HTMLElement).isContentEditable) {
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      sel.deleteFromDocument();
      sel.getRangeAt(0).insertNode(document.createTextNode(text));
    } else {
      (target as HTMLElement).append(text);
    }
  }
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === 'GENZ_INSERT_TEXT' && typeof msg.text === 'string') {
    const target = (document.activeElement as HTMLElement) || lastFocused;
    if (target) insertTextAtTarget(target, msg.text);
  }
});

function init() {
  try {
    scan();
    observer.observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener('readystatechange', () => {
      if (document.readyState === 'complete') scan();
    });
  } catch (e) {
    console.error('[genz] content init error', e);
  }
}

init(); 