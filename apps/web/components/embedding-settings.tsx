"use client";

import { FormEvent, useEffect, useState } from "react";

type Settings = {
  provider: string;
  embedding_calls_enabled: boolean;
  api_key_configured: boolean;
  storage: string;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function EmbeddingSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [status, setStatus] = useState("Loading local embedding settings…");

  async function refresh() {
    const response = await fetch(`${apiBase}/api/settings/embeddings`);
    if (!response.ok) throw new Error("Settings are unavailable. Is the local API running?");
    const next = (await response.json()) as Settings;
    setSettings(next);
    setEnabled(next.embedding_calls_enabled);
    setStatus(next.embedding_calls_enabled ? "Embedding calls enabled locally." : "Embedding calls disabled.");
  }

  useEffect(() => { void refresh().catch((error: Error) => setStatus(error.message)); }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("Saving local setting…");
    try {
      const response = await fetch(`${apiBase}/api/settings/embeddings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(enabled ? {
          provider: "openai",
          embedding_calls_enabled: true,
          api_key: apiKey,
          acknowledge_external_data_transfer_and_cost: acknowledged,
        } : { provider: "disabled", embedding_calls_enabled: false }),
      });
      const payload = await response.json() as Settings | { detail?: string };
      if (!response.ok) throw new Error("detail" in payload ? String(payload.detail) : "Unable to update setting");
      setSettings(payload as Settings);
      setApiKey(""); // Never keep it in component state after submission.
      setStatus(enabled ? "Embedding calls enabled locally; semantic indexing is not enabled yet." : "Embedding calls disabled and in-memory key cleared.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to update setting");
    }
  }

  return (
    <section className="panel settings-panel">
      <div className="section-heading"><div><p className="eyebrow">LOCAL DEVELOPMENT ONLY</p><h2>Embedding provider</h2></div><span className={settings?.embedding_calls_enabled ? "badge warning" : "badge secure"}>{settings?.embedding_calls_enabled ? "Enabled" : "Disabled"}</span></div>
      <p className="notice">A key is never saved to this browser, `.env`, logs, or the database. It stays in API memory only and is erased when disabled or restarted. When enabled, indexed source text and semantic-search queries may be sent to the provider.</p>
      <form onSubmit={save}>
        <label className="toggle-row">
          <input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />
          <span>Allow embedding API calls</span>
        </label>
        {enabled && <>
          <label htmlFor="embedding-api-key">OpenAI API key</label>
          <input id="embedding-api-key" type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} autoComplete="off" spellCheck="false" minLength={20} maxLength={512} required />
          <label className="acknowledgement"><input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} required /> I understand indexed source text and semantic-search queries may be sent to the provider and may incur cost.</label>
        </>}
        <button type="submit">{enabled ? "Enable local embedding calls" : "Disable and clear key"}</button>
      </form>
      <p className="status" role="status">{status}</p>
    </section>
  );
}
