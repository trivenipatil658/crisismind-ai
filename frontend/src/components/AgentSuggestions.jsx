const ICONS = {
  "Medical Agent": "🏥", "Rescue Agent": "🚒", "Transport Agent": "🚌",
  "Shelter Agent": "🏠", "NGO Agent": "🤝", "Fire & Safety Agent": "🔥",
  "Resource Agent": "📦", "Safety Agent": "🛡️",
};

export default function AgentSuggestions({ suggestions }) {
  return (
    <div className="card">
      <h2 className="section-title">🤖 Multi-Agent Suggestions</h2>
      <div className="agents-grid">
        {suggestions.map((s, i) => (
          <div key={i} className="agent-card">
            <div className="agent-header">
              <span className="agent-icon">{ICONS[s.agent] || "🔍"}</span>
              <strong>{s.agent}</strong>
              <span className={`agent-llm-tag ${s.llm_enriched ? "tag-llm" : "tag-rule"}`}>
                {s.llm_enriched ? "🤖 LLM" : "⚙️ Rule"}
              </span>
            </div>
            <p className="agent-suggestion">{s.suggestion}</p>
            <div className="pros-cons">
              <div>
                <strong className="pros-label">Pros</strong>
                <ul>{s.pros.map((p, j) => <li key={j}>{p}</li>)}</ul>
              </div>
              <div>
                <strong className="cons-label">Cons</strong>
                <ul>{s.cons.map((c, j) => <li key={j}>{c}</li>)}</ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
