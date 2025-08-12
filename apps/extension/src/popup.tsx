import { useEffect, useState } from 'react';
import './popup.css';
import { apiLogin } from './api';
import { getSettings, saveSettings } from './storage';

export default function Popup() {
  const [model, setModel] = useState('gpt-4o-mini');
  const [provider, setProvider] = useState<'openai' | 'anthropic' | 'gemini'>('openai');
  const [tone, setTone] = useState('concise');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState<string | undefined>(undefined);
  const [includeSelectionDefault, setIncludeSelectionDefault] = useState(false);
  const [defaultModels, setDefaultModels] = useState<{ openai?: string; anthropic?: string; gemini?: string }>({});
  const [disabled, setDisabled] = useState(false);
  const [currentDomain, setCurrentDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSettings().then((s) => {
      setToken(s.authToken);
      if (s.defaultProvider) setProvider(s.defaultProvider);
      if (s.defaultModel) setModel(s.defaultModel);
      if (s.defaultTone) setTone(s.defaultTone);
      setIncludeSelectionDefault(!!s.includeSelectionDefault);
      setDefaultModels(s.defaultModels || {});
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const url = tabs[0]?.url || '';
        try {
          const u = new URL(url);
          setCurrentDomain(u.hostname);
          setDisabled((s.disabledDomains || []).includes(u.hostname));
        } catch {}
      });
    });
  }, []);

  async function handleLogin() {
    setError(null);
    setLoading(true);
    try {
      const t = await apiLogin(email, password);
      await saveSettings({ authToken: t });
      setToken(t);
    } catch (e: any) {
      setError(e?.message ?? 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveDefaults() {
    setError(null);
    setLoading(true);
    try {
      await saveSettings({ defaultProvider: provider, defaultModel: model, defaultTone: tone, includeSelectionDefault, defaultModels });
    } catch (e: any) {
      setError(e?.message ?? 'Save failed');
    } finally {
      setLoading(false);
    }
  }

  async function toggleDisabled() {
    const s = await getSettings();
    const list = new Set(s.disabledDomains || []);
    if (disabled) list.delete(currentDomain);
    else list.add(currentDomain);
    await saveSettings({ disabledDomains: Array.from(list) });
    setDisabled(!disabled);
  }

  return (
    <div className="popup">
      <h1>Genz</h1>

      {!token ? (
        <div className="card">
          <h2>Login</h2>
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button disabled={loading} onClick={handleLogin}>Login</button>
        </div>
      ) : (
        <div className="card">
          <h2>Defaults</h2>
          <label>
            Provider
            <select value={provider} onChange={(e) => setProvider(e.target.value as any)}>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Gemini</option>
            </select>
          </label>
          <label>
            Model
            <input value={model} onChange={(e) => setModel(e.target.value)} />
          </label>
          <label>
            Tone
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              <option value="concise">Concise</option>
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="assertive">Assertive</option>
            </select>
          </label>

          <h3 style={{ marginTop: 8, fontSize: 12 }}>Per-provider models</h3>
          <label>
            OpenAI model
            <input value={defaultModels.openai || ''} placeholder="gpt-4o-mini" onChange={(e) => setDefaultModels({ ...defaultModels, openai: e.target.value })} />
          </label>
          <label>
            Anthropic model
            <input value={defaultModels.anthropic || ''} placeholder="claude-3-haiku-20240307" onChange={(e) => setDefaultModels({ ...defaultModels, anthropic: e.target.value })} />
          </label>
          <label>
            Gemini model
            <input value={defaultModels.gemini || ''} placeholder="gemini-1.5-flash" onChange={(e) => setDefaultModels({ ...defaultModels, gemini: e.target.value })} />
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={includeSelectionDefault} onChange={(e) => setIncludeSelectionDefault(e.target.checked)} />
            Include selection by default
          </label>

          <button disabled={loading} onClick={handleSaveDefaults}>Save</button>
        </div>
      )}

      <div className="card">
        <h2>Site</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12 }}>{currentDomain || 'Unknown domain'}</span>
          <button onClick={toggleDisabled}>{disabled ? 'Enable on this site' : 'Disable on this site'}</button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      <footer>Generated by Genz</footer>
    </div>
  );
}

// Mount
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root')!);
root.render(<Popup />);
