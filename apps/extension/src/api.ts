import { getSettings } from "./storage";

export async function apiLogin(
  email: string,
  password: string
): Promise<string> {
  const { apiBaseUrl } = await getSettings();
  const res = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  const data = await res.json();
  return data.access_token as string;
}

export async function apiGenerate(params: {
  model: string;
  provider: "openai" | "anthropic" | "gemini";
  prompt: string;
  tone?: string;
  selectedText?: string;
  pageText?: string;
}): Promise<string> {
  const { apiBaseUrl, authToken } = await getSettings();
  if (!authToken) throw new Error("Not authenticated");
  const body = {
    model: params.model,
    model_provider: params.provider,
    prompt: params.prompt,
    context: {
      selected_text: params.selectedText,
      page_text: params.pageText,
    },
    options: { tone: params.tone, max_tokens: 128, temperature: 0.7 },
    use_user_key: true,
  };
  const res = await fetch(`${apiBaseUrl}/api/v1/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Generate failed: ${res.status}`);
  const data = await res.json();
  return data.output_text as string;
}
