"use client";

import { FormEvent, useState } from "react";

type SearchMode = "keyword" | "semantic" | "hybrid";
type Result = { file_path: string; start_line: number; end_line: number; score: number; content: string };
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [results, setResults] = useState<Result[]>([]);
  const [message, setMessage] = useState("Create and index a local repository before searching.");
  const [repositoryId, setRepositoryId] = useState("");
  const [filePath, setFilePath] = useState("src/example.py");
  const [source, setSource] = useState("def retry_failed_payment(payment_id):\n    return payment_id\n");

  async function ingest() {
    setMessage("Creating local repository and indexing source…");
    const repositoryResponse = await fetch(`${apiBase}/api/repositories`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "local", owner: "local", repository: `workspace-${Date.now()}`, branch: "main" }),
    });
    if (!repositoryResponse.ok) throw new Error("Could not create local repository");
    const repository = await repositoryResponse.json() as { repository: { id: string } };
    const documentResponse = await fetch(`${apiBase}/api/repositories/${repository.repository.id}/documents`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath, content: source }),
    });
    if (!documentResponse.ok) throw new Error("Could not index source; check file path and size");
    setRepositoryId(repository.repository.id);
    setMessage("Local source indexed. You can search it now.");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!repositoryId) { setMessage("Index local source first."); return; }
    setMessage("Searching…");
    try {
      const response = await fetch(`${apiBase}/api/search`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, repository_id: repositoryId, mode }),
      });
      if (!response.ok) throw new Error("Search failed");
      const payload = await response.json() as { results: Result[]; effective_mode: string; semantic_enabled: boolean };
      setResults(payload.results);
      setMessage(payload.semantic_enabled ? `Showing ${payload.effective_mode} results.` : `Showing ${payload.effective_mode} results; embeddings are disabled.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Search failed"); }
  }

  return (
    <section className="panel">
      <div className="ingest">
        <label htmlFor="file-path">Local source file</label>
        <input id="file-path" value={filePath} onChange={(event) => setFilePath(event.target.value)} maxLength={1024} />
        <textarea aria-label="Local source code" value={source} onChange={(event) => setSource(event.target.value)} maxLength={1048576} />
        <button type="button" onClick={() => void ingest().catch((error: Error) => setMessage(error.message))}>Index local source</button>
      </div>
      <form onSubmit={submit}>
        <label htmlFor="query">Ask the codebase</label>
        <div className="search-row">
          <input id="query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Where are failed payments retried?" minLength={2} maxLength={2000} required />
          <button type="submit">Search</button>
        </div>
        <fieldset>
          <legend>Retrieval mode</legend>
          {(["keyword", "semantic", "hybrid"] as SearchMode[]).map((option) => (
            <label className="mode" key={option}>
              <input type="radio" name="mode" value={option} checked={mode === option} onChange={() => setMode(option)} />
              {option}
            </label>
          ))}
        </fieldset>
      </form>
      <p className="status" role="status">{message}{repositoryId && <><br /><small>Repository ready: {repositoryId.slice(0, 8)}…</small></>}</p>
      {results.map((result) => <article className="result" key={`${result.file_path}:${result.start_line}`}><strong>{result.file_path}</strong><span>Lines {result.start_line}–{result.end_line} · {(result.score * 100).toFixed(0)}%</span><pre>{result.content}</pre></article>)}
    </section>
  );
}
