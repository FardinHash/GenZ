chrome.runtime.onInstalled.addListener(() => {
  console.debug("[genz] extension installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "PING") {
    sendResponse({ ok: true });
    return true;
  }
});
