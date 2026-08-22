import { SearchPanel } from "../components/search-panel";
import { EmbeddingSettings } from "../components/embedding-settings";
import { ReviewPanel } from "../components/review-panel";

export default function Home() {
  return (
    <main>
      <header>
        <p className="eyebrow">LOCAL-ONLY MVP · SECURITY GATE ACTIVE</p>
        <h1>Developer Intelligence</h1>
        <p className="subtitle">Hybrid code search and evidence-backed pull-request reviews.</p>
      </header>
      <SearchPanel />
      <EmbeddingSettings />
      <ReviewPanel />
      <section className="grid">
        <article className="card"><h2>Repository ingestion</h2><p>Queued, bounded, and not yet connected to GitHub. No repository content leaves local development.</p><span className="badge">Foundation</span></article>
        <article className="card"><h2>Patch evidence</h2><p>Paste a local unified diff to retrieve stored, repository-scoped source context for every changed hunk.</p><span className="badge secure">Local-only</span></article>
        <article className="card"><h2>Security checkpoint</h2><p>External review is required before OAuth, webhooks, public access, or deployment.</p><span className="badge secure">Required</span></article>
      </section>
    </main>
  );
}
