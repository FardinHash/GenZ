import { apiGenerate } from "./api";
import { getSettings } from "./storage";

chrome.runtime.onInstalled.addListener(() => {
  console.debug("[genz] extension installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "PING") {
    sendResponse({ ok: true });
    return true;
  }
  if (message?.type === "GENZ_REQUEST_GENERATE") {
    (async () => {
      try {
        const { defaultProvider, defaultModel, defaultTone } =
          await getSettings();
        const text = await apiGenerate({
          model: defaultModel ?? "gpt-4o-mini",
          provider: (defaultProvider ?? "openai") as "openai",
          prompt: message.selectedText || "Compose a helpful reply.",
          tone: defaultTone ?? "concise",
          selectedText: message.selectedText,
        });
        sendResponse({ ok: true, text });
      } catch (e: any) {
        sendResponse({ ok: false, error: e?.message ?? "Failed to generate" });
      }
    })();
    return true;
  }
});
