"use client";
import { useEffect, useState } from "react";
import { api, getToken, setToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [keys, setKeys] = useState<any[]>([]);
  const [provider, setProvider] = useState<"openai" | "anthropic" | "gemini">(
    "openai"
  );
  const [keyValue, setKeyValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        const list = await api.listKeys();
        setKeys(list);
      } catch (e: any) {
        setError(e?.message ?? "Failed to load");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function addKey() {
    setError(null);
    try {
      await api.createKey(provider, keyValue);
      setKeyValue("");
      const list = await api.listKeys();
      setKeys(list);
    } catch (e: any) {
      setError(e?.message ?? "Failed to add key");
    }
  }

  async function deleteKey(id: string) {
    setError(null);
    try {
      await api.deleteKey(id);
      setKeys((prev) => prev.filter((k) => k.id !== id));
    } catch (e: any) {
      setError(e?.message ?? "Failed to delete");
    }
  }

  function logout() {
    setToken(null);
    router.push("/login");
  }

  if (loading) return <main style={{ padding: 24 }}>Loading...</main>;

  return (
    <main style={{ padding: 24 }}>
      <h1>Dashboard</h1>
      {error && <div style={{ color: "crimson" }}>{error}</div>}
      {user && (
        <div style={{ marginBottom: 12 }}>
          <div>Email: {user.email}</div>
          <div>Plan: {user.plan_id ?? "basic"}</div>
          <button onClick={logout}>Logout</button>
        </div>
      )}

      <section
        style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}
      >
        <h2>Provider API Keys</h2>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as any)}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic" disabled>
              Anthropic (soon)
            </option>
            <option value="gemini" disabled>
              Gemini (soon)
            </option>
          </select>
          <input
            placeholder="API key"
            value={keyValue}
            onChange={(e) => setKeyValue(e.target.value)}
          />
          <button onClick={addKey}>Add</button>
        </div>
        <ul>
          {keys.map((k) => (
            <li
              key={k.id}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span style={{ width: 90 }}>{k.provider}</span>
              <span style={{ flex: 1 }}>••••••••••••</span>
              <button onClick={() => deleteKey(k.id)}>Delete</button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
