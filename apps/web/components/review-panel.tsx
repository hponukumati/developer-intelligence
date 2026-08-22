"use client";

import { FormEvent, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
type Evidence = {
  status: "matched" | "no_local_context";
  changed_file_path: string;
  changed_start_line: number;
  changed_end_line: number;
  file_path?: string;
  start_line?: number;
  end_line?: number;
  excerpt?: string;
};

export function ReviewPanel() {
  const [repositoryId, setRepositoryId] = useState("");
  const [pr, setPr] = useState("");
  const [patch, setPatch] = useState("diff --git a/src/example.py b/src/example.py\n--- a/src/example.py\n+++ b/src/example.py\n@@ -1,1 +1,2 @@\n def retry_failed_payment(payment_id):\n+    return payment_id\n");
  const [status, setStatus] = useState("Paste a unified diff to create a local evidence brief.");
  const [evidence, setEvidence] = useState<Evidence[]>([]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEvidence([]);
    try {
      const response = await fetch(`${apiBase}/api/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repository_id: repositoryId,
          pull_request_number: pr ? Number(pr) : null,
          patch,
        }),
      });
      const payload = await response.json() as { review_id?: string; evidence?: Evidence[]; detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "Unable to create local review");
      setEvidence(payload.evidence ?? []);
      setStatus(`Local evidence brief created: ${payload.review_id?.slice(0, 8) ?? "review"}…`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to create local review");
    }
  }

  return (
    <section className="panel settings-panel">
      <h2>Local patch evidence</h2>
      <p className="notice">Paste a unified diff from an indexed local repository. This is local evidence assistance—not GitHub-connected, AI-generated, or a publishable code review.</p>
      <form onSubmit={submit}>
        <label htmlFor="review-repo">Indexed repository ID</label>
        <input id="review-repo" value={repositoryId} onChange={(event) => setRepositoryId(event.target.value)} required />
        <label htmlFor="pr-number">Pull request number (optional local label)</label>
        <input id="pr-number" type="number" min="1" value={pr} onChange={(event) => setPr(event.target.value)} />
        <label htmlFor="patch">Unified diff</label>
        <textarea id="patch" value={patch} onChange={(event) => setPatch(event.target.value)} maxLength={1048576} required />
        <button type="submit">Create local evidence brief</button>
      </form>
      <p className="status" role="status">{status}</p>
      {evidence.map((item, index) => (
        <article className="result" key={`${item.changed_file_path}:${item.changed_start_line}:${index}`}>
          <strong>{item.changed_file_path} · lines {item.changed_start_line}–{item.changed_end_line}</strong>
          {item.status === "no_local_context" ? <span>No indexed local context overlapped this changed hunk.</span> : <><span>Indexed context: {item.file_path} · lines {item.start_line}–{item.end_line}</span><pre>{item.excerpt}</pre></>}
        </article>
      ))}
    </section>
  );
}
