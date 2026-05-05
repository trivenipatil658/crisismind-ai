import { useEffect, useState } from "react";
import { fetchLLMStatus } from "../api";

export default function LLMStatus() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetchLLMStatus()
      .then(setStatus)
      .catch(() => setStatus({ ollama_available: false, model: null, mode: "Rule-Based Fallback" }));
  }, []);

  if (!status) return null;

  return (
    <div className={`llm-status-bar ${status.ollama_available ? "llm-online" : "llm-offline"}`}>
      <span className={`llm-dot ${status.ollama_available ? "dot-online" : "dot-offline"}`}></span>
      <span className="llm-label">
        Ollama Local LLM:&nbsp;
        <strong>{status.ollama_available ? "Online" : "Offline"}</strong>
      </span>
      {status.ollama_available && (
        <span className="llm-model">Model: {status.model}</span>
      )}
      <span className="llm-mode">{status.mode}</span>
      {!status.ollama_available && (
        <span className="llm-fallback-note">Using rule-based explanations (no API key needed)</span>
      )}
    </div>
  );
}
