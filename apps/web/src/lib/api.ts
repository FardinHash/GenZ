const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("genz_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("genz_token", token);
  else localStorage.removeItem("genz_token");
}

async function doFetch(path: string, init: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}

async function request(path: string, init: RequestInit = {}, retry = true): Promise<any> {
  let res = await doFetch(path, init);
  if (res.status === 401 && retry) {
    const r = await doFetch('/api/v1/auth/refresh', { method: 'POST' });
    if (r.ok) {
      const data = await r.json();
      setToken(data.access_token);
      res = await doFetch(path, init);
    }
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  signup: (email: string, password: string) =>
    request("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: async (email: string, password: string) => {
    const res = await request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    return res;
  },
  me: () => request("/api/v1/user/me"),
  myUsage: () => request('/api/v1/user/usage'),
  listKeys: () => request("/api/v1/keys"),
  createKey: (
    provider: "openai" | "anthropic" | "gemini",
    key: string,
    key_type = "user_provided"
  ) =>
    request("/api/v1/keys", {
      method: "POST",
      body: JSON.stringify({ provider, key, key_type }),
    }),
  deleteKey: (id: string) =>
    request(`/api/v1/keys/${id}`, { method: "DELETE" }),
  listRequests: (limit = 50) => request(`/api/v1/requests?limit=${limit}`),
};
