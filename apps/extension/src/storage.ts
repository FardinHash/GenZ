export type GenzSettings = {
  apiBaseUrl: string;
  authToken?: string;
  defaultProvider?: 'openai' | 'anthropic' | 'gemini';
  defaultModel?: string;
  defaultTone?: string;
  includeSelectionDefault?: boolean;
  defaultModels?: {
    openai?: string;
    anthropic?: string;
    gemini?: string;
  };
  disabledDomains?: string[];
};

const STORAGE_KEY = 'genz:settings';

export async function getSettings(): Promise<GenzSettings> {
  const res = await chrome.storage.local.get(STORAGE_KEY);
  const val = (res?.[STORAGE_KEY] ?? {}) as Partial<GenzSettings>;
  return {
    apiBaseUrl: val.apiBaseUrl ?? 'http://localhost:8000',
    authToken: val.authToken,
    defaultProvider: val.defaultProvider ?? 'openai',
    defaultModel: val.defaultModel ?? 'gpt-4o-mini',
    defaultTone: val.defaultTone ?? 'concise',
    includeSelectionDefault: val.includeSelectionDefault ?? false,
    defaultModels: val.defaultModels ?? { openai: 'gpt-4o-mini', anthropic: 'claude-3-haiku-20240307', gemini: 'gemini-1.5-flash' },
    disabledDomains: val.disabledDomains ?? [],
  };
}

export async function saveSettings(next: Partial<GenzSettings>): Promise<void> {
  const cur = await getSettings();
  const merged: GenzSettings = { ...cur, ...next } as GenzSettings;
  await chrome.storage.local.set({ [STORAGE_KEY]: merged });
}
