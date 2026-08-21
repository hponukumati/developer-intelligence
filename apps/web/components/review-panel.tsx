"use client";

import { FormEvent, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function ReviewPanel() {
  const [repositoryId, setRepositoryId] = useState("");
  const [pr, setPr] = useState("");
  const [status, setStatus] = useState("Local review queue only; GitHub is disconnected.");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const response = await fetch(`${apiBase}/api/reviews`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repository_id: repositoryId, pull_request_number: Number(pr) }),
      });
      const payload = await response.json() as { message?: string; detail?: string };
      setStatus(response.ok ? payload.message ?? "Queued" : payload.detail ?? "Unable to queue review");
    } catch { setStatus("Local API is unavailable"); }
  }

  return <section className="panel settings-panel"><h2>PR review</h2><p className="notice">This creates a local review request only. It cannot fetch GitHub, publish comments, or use credentials.</p><form onSubmit={submit}><label htmlFor="review-repo">Indexed repository ID</label><input id="review-repo" value={repositoryId} onChange={(e) => setRepositoryId(e.target.value)} required /><label htmlFor="pr-number">Pull request number</label><input id="pr-number" type="number" min="1" value={pr} onChange={(e) => setPr(e.target.value)} required /><button type="submit">Queue local review</button></form><p className="status">{status}</p></section>;
}
