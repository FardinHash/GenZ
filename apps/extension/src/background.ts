import { apiGenerate } from './api';
import { getSettings } from './storage';

chrome.runtime.onInstalled.addListener(() => {
  console.debug('[genz] extension installed');
});

const streams = new Map<number, AbortController>();

async function getActiveTabMeta(tabId: number) {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs.find((t) => t.id === tabId) || tabs[0];
    return { url: tab?.url || '', title: tab?.title || '' };
  } catch {
    return { url: '', title: '' };
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'PING') {
    sendResponse({ ok: true });
    return true;
  }
  if (message?.type === 'GENZ_REQUEST_GENERATE') {
    (async () => {
      try {
        const { defaultProvider, defaultModel, defaultTone, includeSelectionDefault } = await getSettings();
        const selectedText = message.includeSelection === false ? '' : (message.selectedText || (includeSelectionDefault ? message.selectedText : ''));
        const { url, title } = sender?.tab?.id ? await getActiveTabMeta(sender.tab.id) : { url: '', title: '' };
        const res = await fetch(`${(await getSettings()).apiBaseUrl}/api/v1/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${(await getSettings()).authToken}` },
          body: JSON.stringify({
            model: defaultModel ?? 'gpt-4o-mini',
            model_provider: (defaultProvider ?? 'openai') as 'openai',
            prompt: selectedText || 'Compose a helpful reply.',
            context: { selected_text: selectedText, url, title },
            options: { tone: defaultTone ?? 'concise', max_tokens: 128, temperature: 0.7 },
            use_user_key: true,
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        sendResponse({ ok: true, text: data.output_text });
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
      const { apiBaseUrl, authToken, defaultProvider, defaultModel, defaultTone, includeSelectionDefault } = await getSettings();
      if (!authToken) {
        chrome.tabs.sendMessage(tabId, { type: 'GENZ_STREAM_ERROR', error: 'Not authenticated' });
        return;
      }
      const selectedText = message.includeSelection === false ? '' : (message.selectedText || (includeSelectionDefault ? message.selectedText : ''));
      const { url, title } = await getActiveTabMeta(tabId);
      const body = {
        model: message.model || defaultModel || 'gpt-4o-mini',
        model_provider: message.provider || defaultProvider || 'openai',
        prompt: selectedText || 'Compose a helpful reply.',
        context: { selected_text: selectedText || '', url, title },
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
