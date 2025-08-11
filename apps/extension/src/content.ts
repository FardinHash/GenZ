const INJECTED_ATTR = "data-genz-injected";
let lastFocused: HTMLElement | null = null;
let lastSelectionText: string = "";

const SELECTOR =
  'textarea, input[type="text"], input[type="search"], input[type="email"], input[type="url"], input[type="tel"], [contenteditable="true"]';

const lastRangeByEditable = new WeakMap<HTMLElement, Range>();

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

function createPopover() {
  const wrap = document.createElement("div");
  wrap.style.position = "absolute";
  wrap.style.zIndex = "2147483647";
  wrap.style.minWidth = "280px";
  wrap.style.maxWidth = "420px";
  wrap.style.background = "#fff";
  wrap.style.border = "1px solid #e5e7eb";
  wrap.style.borderRadius = "8px";
  wrap.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
  wrap.style.padding = "8px";
  wrap.style.fontFamily =
    "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial";

  const title = document.createElement("div");
  title.textContent = "Compose with AI";
  title.style.fontSize = "12px";
  title.style.color = "#111";
  title.style.marginBottom = "6px";

  const actions = document.createElement("div");
  actions.style.display = "flex";
  actions.style.gap = "6px";
  actions.style.marginBottom = "6px";

  const btnStart = document.createElement("button");
  btnStart.textContent = "Generate";
  const btnCancel = document.createElement("button");
  btnCancel.textContent = "Cancel";
  const btnInsert = document.createElement("button");
  btnInsert.textContent = "Insert";

  [btnStart, btnCancel, btnInsert].forEach((b) => {
    b.style.fontSize = "12px";
    b.style.padding = "4px 8px";
    b.style.border = "1px solid #d1d5db";
    b.style.borderRadius = "6px";
    b.style.background = "#fff";
    b.style.cursor = "pointer";
  });

  const output = document.createElement("div");
  output.style.fontSize = "12px";
  output.style.whiteSpace = "pre-wrap";
  output.style.border = "1px dashed #e5e7eb";
  output.style.borderRadius = "6px";
  output.style.padding = "6px";
  output.style.minHeight = "40px";

  const includeWrap = document.createElement("label");
  includeWrap.style.display = "flex";
  includeWrap.style.alignItems = "center";
  includeWrap.style.gap = "6px";
  includeWrap.style.fontSize = "12px";
  const includeCb = document.createElement("input");
  includeCb.type = "checkbox";
  const includeTxt = document.createElement("span");
  includeTxt.textContent = "Include selection";
  includeWrap.append(includeCb, includeTxt);

  actions.append(btnStart, btnCancel, btnInsert);
  wrap.append(title, actions, includeWrap, output);

  return { wrap, btnStart, btnCancel, btnInsert, output, includeCb };
}

let currentPopover: ReturnType<typeof createPopover> | null = null;

function positionPopover(
  pop: ReturnType<typeof createPopover>,
  anchor: HTMLElement
) {
  const rect = anchor.getBoundingClientRect();
  pop.wrap.style.top = `${window.scrollY + rect.bottom + 6}px`;
  pop.wrap.style.left = `${window.scrollX + rect.left}px`;
}

function openPopover(target: HTMLElement) {
  if (currentPopover) closePopover();
  const pop = createPopover();
  currentPopover = pop;
  document.body.appendChild(pop.wrap);
  positionPopover(pop, target);

  let streaming = false;
  let buffer = "";

  const start = async () => {
    if (streaming) return;
    streaming = true;
    buffer = "";
    pop.output.textContent = "";
    const selection =
      (window.getSelection()?.toString() ?? "").trim() ||
      lastSelectionText ||
      "";
    chrome.runtime.sendMessage({
      type: "GENZ_STREAM_START",
      selectedText: selection,
      includeSelection: !!pop.includeCb.checked,
    });
  };
  const cancel = async () => {
    if (!streaming) return;
    chrome.runtime.sendMessage({ type: "GENZ_STREAM_CANCEL" });
  };
  const insert = async () => {
    if (!buffer) return;
    insertTextAtTarget(target, buffer);
    closePopover();
  };

  pop.btnStart.addEventListener("click", start);
  pop.btnCancel.addEventListener("click", cancel);
  pop.btnInsert.addEventListener("click", (e) => {
    e.preventDefault();
    insert();
  });

  const onMsg = (msg: any) => {
    if (msg?.type === "GENZ_STREAM_BEGIN") {
      pop.output.textContent = "";
    } else if (
      msg?.type === "GENZ_STREAM_DELTA" &&
      typeof msg.delta === "string"
    ) {
      buffer += msg.delta;
      pop.output.textContent = buffer;
    } else if (msg?.type === "GENZ_STREAM_DONE") {
      streaming = false;
    } else if (msg?.type === "GENZ_STREAM_ABORTED") {
      streaming = false;
    } else if (msg?.type === "GENZ_STREAM_ERROR") {
      streaming = false;
      pop.output.textContent = `Error: ${msg.error}`;
    }
  };

  const listener = (msg: any, _sender: any) => onMsg(msg);
  chrome.runtime.onMessage.addListener(listener);

  const onScrollOrResize = () => positionPopover(pop, target);
  window.addEventListener("scroll", onScrollOrResize, { passive: true });
  window.addEventListener("resize", onScrollOrResize, { passive: true });

  const onBlurDetach = () => {
    setTimeout(() => {
      if (document.activeElement !== target) closePopover();
    }, 100);
  };
  target.addEventListener("blur", onBlurDetach);

  function closePopover() {
    try {
      chrome.runtime.onMessage.removeListener(listener);
      window.removeEventListener("scroll", onScrollOrResize);
      window.removeEventListener("resize", onScrollOrResize);
      target.removeEventListener("blur", onBlurDetach);
      pop.wrap.remove();
      if (streaming) chrome.runtime.sendMessage({ type: "GENZ_STREAM_CANCEL" });
    } catch {}
    currentPopover = null;
  }
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
      openPopover(target);
    } catch (e) {
      console.error("[genz] popover failed", e);
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

function findEditableAncestor(node: Node | null): HTMLElement | null {
  let cur: Node | null = node;
  while (cur) {
    if (cur instanceof HTMLElement && cur.isContentEditable) return cur;
    cur = cur.parentNode;
  }
  return null;
}

function trackSelection() {
  const handler = () => {
    const sel = window.getSelection();
    const sText = sel?.toString() ?? "";
    if (sText) lastSelectionText = sText;
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0).cloneRange();
      const editable = findEditableAncestor(range.startContainer);
      if (editable) lastRangeByEditable.set(editable, range);
    }
  };
  document.addEventListener("selectionchange", handler, { passive: true });
}

function insertTextAtTarget(target: HTMLElement, text: string) {
  if (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement
  ) {
    target.focus();
    const start = target.selectionStart ?? target.value.length;
    const end = target.selectionEnd ?? start;
    const before = target.value.slice(0, start);
    const after = target.value.slice(end);
    target.value = before + text + after;
    const caret = start + text.length;
    try {
      target.setSelectionRange(caret, caret);
    } catch {}
    target.dispatchEvent(new Event("input", { bubbles: true }));
    return;
  }
  if ((target as HTMLElement).isContentEditable) {
    target.focus();
    let range = lastRangeByEditable.get(target as HTMLElement);
    const sel = window.getSelection();
    if (!range) {
      range = document.createRange();
      range.selectNodeContents(target);
      range.collapse(false);
    }
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
    range.insertNode(document.createTextNode(text));
    range.setStartAfter(range.endContainer);
    range.collapse(false);
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
    target.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === "GENZ_INSERT_TEXT" && typeof msg.text === "string") {
    const target = (document.activeElement as HTMLElement) || lastFocused;
    if (target) insertTextAtTarget(target, msg.text);
  }
});

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

init();
