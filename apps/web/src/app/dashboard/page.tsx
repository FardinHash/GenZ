"use client";
import { useEffect, useState } from "react";
import { api, getToken, setToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [keys, setKeys] = useState<any[]>([]);
  const [provider, setProvider] = useState<"openai" | "anthropic" | "gemini">(
    "openai"
  );
  const [keyValue, setKeyValue] = useState("");
  const [requests, setRequests] = useState<any[]>([]);
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
        const [list, reqs, u] = await Promise.all([
          api.listKeys(),
          api.listRequests(50),
          api.myUsage(),
        ]);
        setKeys(list);
        setRequests(reqs);
        setUsage(u);
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

  async function onSubscribe(plan: "Basic" | "Pro" | "Premium") {
    setError(null);
    try {
      const res = await api.billingSubscribe(plan);
      if (res.checkout_url) window.location.href = res.checkout_url as string;
    } catch (e: any) {
      setError(e?.message ?? "Checkout failed");
    }
  }

  async function onPortal() {
    setError(null);
    try {
      const res = await api.billingPortal();
      if (res.portal_url) window.location.href = res.portal_url as string;
    } catch (e: any) {
      setError(e?.message ?? "Portal failed");
    }
  }

  if (loading) return <main style={{ padding: 24 }}>Loading...</main>;

  return (
    <main style={{ padding: 24 }}>
      <h1>Dashboard</h1>
      {error && <div style={{ color: "crimson" }}>{error}</div>}
      {user && (
        <div style={{ marginBottom: 12 }}>
          <div>Email: {user.email}</div>
          <div>Plan: {usage?.plan?.name || user.plan_id || "basic"}</div>
          <button onClick={logout}>Logout</button>
        </div>
      )}

      {usage && (
        <section
          style={{
            border: "1px solid #eee",
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          <h2>Your Usage</h2>
          <div
            style={{ display: "flex", gap: 16, fontSize: 12, flexWrap: "wrap" }}
          >
            <div>Total requests: {usage.total}</div>
            <div>Tokens in: {usage.tokens_in}</div>
            <div>Tokens out: {usage.tokens_out}</div>
            <div>
              Cost (USD): {usage.cost_usd?.toFixed?.(6) ?? usage.cost_usd}
            </div>
            <div>Plan quota: {usage.plan?.token_quota}</div>
            <div>Monthly used: {usage.monthly_used}</div>
            <div>Monthly remaining: {usage.monthly_remaining}</div>
          </div>
        </section>
      )}

      <section
        style={{
          border: "1px solid #eee",
          padding: 12,
          borderRadius: 8,
          marginBottom: 16,
        }}
      >
        <h2>Plan</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={() => onSubscribe("Basic")}>Switch to Basic</button>
          <button onClick={() => onSubscribe("Pro")}>Upgrade to Pro</button>
          <button onClick={() => onSubscribe("Premium")}>
            Upgrade to Premium
          </button>
          <button onClick={onPortal}>Manage Billing</button>
        </div>
      </section>

      <section
        style={{
          border: "1px solid #eee",
          padding: 12,
          borderRadius: 8,
          marginBottom: 16,
        }}
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

      <section
        style={{ border: "1px solid #eee", padding: 12, borderRadius: 8 }}
      >
        <h2>Recent Requests</h2>
        <table style={{ width: "100%", fontSize: 12 }}>
          <thead>
            <tr>
              <th align="left">When</th>
              <th align="left">Provider</th>
              <th align="left">Model</th>
              <th align="left">Domain</th>
              <th align="left">Path</th>
              <th align="left">Status</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.model_provider}</td>
                <td>{r.model}</td>
                <td>{r.domain || "-"}</td>
                <td
                  style={{
                    maxWidth: 280,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {r.path || "-"}
                </td>
                <td>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
