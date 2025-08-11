import { apiGenerate } from './api';
import { getSettings } from './storage';

chrome.runtime.onInstalled.addListener(() => {
  console.debug('[genz] extension installed');
});

const streams = new Map<number, AbortController>();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'PING') {
    sendResponse({ ok: true });
    return true;
  }
  if (message?.type === 'GENZ_REQUEST_GENERATE') {
    (async () => {
      try {
        const { defaultProvider, defaultModel, defaultTone } = await getSettings();
        const text = await apiGenerate({
          model: defaultModel ?? 'gpt-4o-mini',
          provider: (defaultProvider ?? 'openai') as 'openai',
          prompt: message.selectedText || 'Compose a helpful reply.',
          tone: defaultTone ?? 'concise',
          selectedText: message.selectedText,
        });
        sendResponse({ ok: true, text });
      } catch (e: any) {
        sendResponse({ ok: false, error: e?.message ?? 'Failed to generate' });
      }
    })();
    return true;
  }
  if (message?.type === 'GENZ_STREAM_START') {
    const tabId = sender?.tab?.id;
    if (tabId == null) {
      sendResponse({ ok: false, error: 'Missing tab' });
      return true;
    }
    (async () => {
      const { apiBaseUrl, authToken, defaultProvider, defaultModel, defaultTone } = await getSettings();
      if (!authToken) {
        chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_ERROR', error: 'Not authenticated' });
        return;
      }
      const body = {
        model: message.model || defaultModel || 'gpt-4o-mini',
        model_provider: message.provider || defaultProvider || 'openai',
        prompt: message.selectedText || 'Compose a helpful reply.',
        context: { selected_text: message.selectedText || '' },
        options: { tone: message.tone || defaultTone || 'concise', max_tokens: 256, temperature: 0.7 },
        use_user_key: true,
      };
      const controller = new AbortController();
      streams.set(tabId, controller);
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/generate/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) {
          chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_ERROR', error: `HTTP ${res.status}` });
          streams.delete(tabId);
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_BEGIN' });
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const chunk = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                  chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_DONE' });
                } else if (data) {
                  chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_DELTA', delta: data });
                }
              }
            }
          }
        }
        if (buffer.trim().length > 0) {
          // flush any trailing event
          const lines = buffer.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data && data !== '[DONE]') {
                chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_DELTA', delta: data });
              }
            }
          }
          chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_DONE' });
        }
      } catch (e: any) {
        if (controller.signal.aborted) {
          chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_ABORTED' });
        } else {
          chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_ERROR', error: e?.message || 'Stream failed' });
        }
      } finally {
        streams.delete(tabId);
      }
    })();
    sendResponse({ ok: true });
    return true;
  }
  if (message?.type === 'GENZ_STREAM_CANCEL') {
    const tabId = sender?.tab?.id;
    if (tabId != null) {
      const ctrl = streams.get(tabId);
      if (ctrl) ctrl.abort();
      streams.delete(tabId);
    }
    sendResponse({ ok: true });
    return true;
  }
});
