export type GenzSettings = {
  apiBaseUrl: string;
  authToken?: string;
};

const STORAGE_KEY = "genz:settings";

export async function getSettings(): Promise<GenzSettings> {
  const res = await chrome.storage.local.get(STORAGE_KEY);
  const val = (res?.[STORAGE_KEY] ?? {}) as Partial<GenzSettings>;
  return {
    apiBaseUrl: val.apiBaseUrl ?? "http://localhost:8000",
    authToken: val.authToken,
  };
}

export async function saveSettings(next: Partial<GenzSettings>): Promise<void> {
  const cur = await getSettings();
  const merged: GenzSettings = { ...cur, ...next } as GenzSettings;
  await chrome.storage.local.set({ [STORAGE_KEY]: merged });
}
