const INJECTED_ATTR = "data-genz-injected";
let lastFocused: HTMLElement | null = null;
let lastSelectionText: string = "";

const SELECTOR =
  'textarea, input[type="text"], input[type="search"], input[type="email"], input[type="url"], input[type="tel"], [contenteditable="true"]';

function isVisible(el: HTMLElement): boolean {
  const rect = el.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return false;
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden") return false;
  return true;
}

function isEligible(el: Element): boolean {
  if (!(el instanceof HTMLElement)) return false;
  if (!isVisible(el)) return false;

  if (el instanceof HTMLInputElement) {
    if (el.type === "password" || el.type === "hidden") return false;
    if (el.disabled || el.readOnly) return false;
    return (
      el.type === "text" ||
      el.type === "search" ||
      el.type === "email" ||
      el.type === "url" ||
      el.type === "tel"
    );
  }
  if (el instanceof HTMLTextAreaElement) {
    if (el.disabled || el.readOnly) return false;
    return true;
  }
  if (el.isContentEditable !== true) return false;
  return true;
}

function createButton(target: HTMLElement): HTMLButtonElement {
  const btn = document.createElement("button");
  btn.textContent = "Compose with AI";
  btn.setAttribute("type", "button");
  btn.style.marginLeft = "6px";
  btn.style.padding = "4px 8px";
  btn.style.fontSize = "12px";
  btn.style.cursor = "pointer";
  btn.style.borderRadius = "6px";
  btn.style.border = "1px solid #ccc";
  btn.style.background = "#fff";

  btn.addEventListener("click", async () => {
    try {
      const selection = (window.getSelection()?.toString() ?? "").trim();
      const selectedText = selection || lastSelectionText || "";
      const providerInfo = await chrome.runtime.sendMessage({
        type: "GENZ_REQUEST_GENERATE",
        selectedText,
      });
      if (providerInfo && typeof providerInfo.text === "string") {
        insertTextAtTarget(target, providerInfo.text);
      }
    } catch (e) {
      console.error("[genz] generate failed", e);
    }
  });

  return btn;
}

function injectForElement(el: Element) {
  if (!(el instanceof HTMLElement)) return;
  if (el.getAttribute(INJECTED_ATTR) === "1") return;
  if (!isEligible(el)) return;

  const btn = createButton(el);
  el.after(btn);
  el.setAttribute(INJECTED_ATTR, "1");

  el.addEventListener("focus", () => {
    lastFocused = el;
  });
}

function scanRoot(root: ParentNode) {
  if (root instanceof Element && (root.matches?.(SELECTOR) ?? false)) {
    injectForElement(root as Element);
  }
  root.querySelectorAll?.(SELECTOR).forEach(injectForElement);
}

let pendingNodes = new Set<ParentNode>();
let scheduled = false;

function scheduleProcess() {
  if (scheduled) return;
  scheduled = true;
  const runner = () => {
    const nodes = Array.from(pendingNodes);
    pendingNodes.clear();
    scheduled = false;
    for (const n of nodes) scanRoot(n);
  };
  if ("requestIdleCallback" in window) {
    (window as any).requestIdleCallback(runner, { timeout: 200 });
  } else {
    setTimeout(runner, 50);
  }
}

const observer = new MutationObserver((mutations) => {
  for (const m of mutations) {
    m.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        pendingNodes.add(node as ParentNode);
      }
    });
  }
  if (pendingNodes.size > 0) scheduleProcess();
});

function trackSelection() {
  const handler = () => {
    const s = window.getSelection()?.toString() ?? "";
    if (s) lastSelectionText = s;
  };
  document.addEventListener("selectionchange", handler, { passive: true });
}

function init() {
  try {
    scanRoot(document);
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
    });
    document.addEventListener("readystatechange", () => {
      if (document.readyState === "complete") scanRoot(document);
    });
    trackSelection();
  } catch (e) {
    console.error("[genz] content init error", e);
  }
}

function insertTextAtTarget(target: HTMLElement, text: string) {
  if (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement
  ) {
    const sep = target.value ? " " : "";
    target.value += sep + text;
    target.dispatchEvent(new Event("input", { bubbles: true }));
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
  if (msg?.type === "GENZ_INSERT_TEXT" && typeof msg.text === "string") {
    const target = (document.activeElement as HTMLElement) || lastFocused;
    if (target) insertTextAtTarget(target, msg.text);
  }
});

init();
