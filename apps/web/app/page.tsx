import { SearchPanel } from "../components/search-panel";
import { EmbeddingSettings } from "../components/embedding-settings";

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
      <section className="grid">
        <article className="card"><h2>Repository ingestion</h2><p>Queued, bounded, and not yet connected to GitHub. No repository content leaves local development.</p><span className="badge">Foundation</span></article>
        <article className="card"><h2>Review queue</h2><p>Structured review requests are accepted by the API. Agent execution and GitHub publishing remain disabled.</p><span className="badge">Planned</span></article>
        <article className="card"><h2>Security checkpoint</h2><p>External review is required before OAuth, webhooks, public access, or deployment.</p><span className="badge secure">Required</span></article>
      </section>
    </main>
  );
}
