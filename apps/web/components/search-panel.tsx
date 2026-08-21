"use client";

import { FormEvent, useState } from "react";

type SearchMode = "keyword" | "semantic" | "hybrid";
type Result = { file_path: string; start_line: number; end_line: number; score: number; content: string };

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [results, setResults] = useState<Result[]>([]);
  const [message, setMessage] = useState("Create and index a local repository before searching.");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("Search needs an indexed repository ID; API wiring comes with the ingestion milestone.");
    setResults([]);
  }

  return (
    <section className="panel">
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
      <p className="status" role="status">{message}</p>
      {results.map((result) => <article className="result" key={`${result.file_path}:${result.start_line}`}><strong>{result.file_path}</strong><span>Lines {result.start_line}–{result.end_line} · {(result.score * 100).toFixed(0)}%</span><pre>{result.content}</pre></article>)}
    </section>
  );
}
