import { useState } from "react";
import "leaflet/dist/leaflet.css";
import "./styles.css";
import LLMStatus from "./components/LLMStatus";
import RoleSelector from "./components/RoleSelector";
import ResourceDashboard from "./components/ResourceDashboard";
import CrisisForm from "./components/CrisisForm";
import RecommendationCard from "./components/RecommendationCard";
import RouteRecommendation from "./components/RouteRecommendation";
import RouteMap from "./components/RouteMap";
import WorkflowTrace from "./components/WorkflowTrace";
import DecisionComparison from "./components/DecisionComparison";
import AgentSuggestions from "./components/AgentSuggestions";
import ExplainabilityBox from "./components/ExplainabilityBox";
import AIReport from "./components/AIReport";
import History from "./components/History";
import { runSimulation, updateResources } from "./api";
import { DEMO_RESOURCES } from "./demo";

export default function App() {
  const [role, setRole] = useState("Crisis Admin");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleSimulate = async (data) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await runSimulation(data));
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleLoadDemoResources = async () => {
    setDemoLoading(true);
    try {
      for (const res of Object.values(DEMO_RESOURCES)) {
        await updateResources(res);
      }
      setError(null);
      alert("Demo resources loaded for all roles! Now run the simulation.");
    } catch (err) {
      setError(err.message);
    }
    setDemoLoading(false);
  };

  const handleLoadHistory = (sim) => {
    setResult(sim);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">CrisisMind AI</h1>
        <p className="subtitle">Role-Based LangGraph Disaster Response and Route Decision Simulator</p>
        <p className="tagline">Simulate disaster. Track resources. Compare actions. Visualize routes. Choose the safest response.</p>
        <LLMStatus />
      </header>

      <main className="main">
        <RoleSelector selected={role} onSelect={setRole} />

        {role !== "Crisis Admin" && <ResourceDashboard role={role} />}

        {role === "Crisis Admin" && (
          <>
            <div className="card demo-resources-card">
              <h2 className="section-title">⚡ Quick Setup</h2>
              <p className="muted" style={{ marginBottom: "12px" }}>
                Load demo resource data for all roles before running simulation, or ask each role officer to submit their updates.
              </p>
              <button className="btn-secondary" onClick={handleLoadDemoResources} disabled={demoLoading}>
                {demoLoading ? "Loading..." : "📦 Load Demo Resources for All Roles"}
              </button>
            </div>
            <CrisisForm onSubmit={handleSimulate} loading={loading} />
          </>
        )}

        {error && <div className="card error-card"><strong>Error:</strong> {error}</div>}

        {result && (
          <>
            <RecommendationCard result={result} />
            <RouteMap
              lat={result.latitude}
              lng={result.longitude}
              routes={result.route_options}
              recommended={result.recommended_route}
              disasterType={result.disaster_type}
              location={result.location}
              affectedPopulation={20000}
            />
            <RouteRecommendation routes={result.route_options} recommended={result.recommended_route} />
            <WorkflowTrace trace={result.workflow_trace} />
            <DecisionComparison paths={result.decision_paths} recommended={result.recommended_path} />
            <AgentSuggestions suggestions={result.agent_suggestions} />
            <ExplainabilityBox
              explanation={result.explanation}
              scenarios={result.generated_scenarios}
              llmUsed={result.llm_used}
            />
            <AIReport simulationId={result.simulation_id} llmUsed={result.llm_used} />
            <div className="card scenario-card">
              <h2 className="section-title">📋 Scenario Summary</h2>
              <p>{result.scenario_summary}</p>
            </div>
          </>
        )}

        <History onLoad={handleLoadHistory} />
      </main>

      <footer className="footer">
        <p>CrisisMind AI | FastAPI + LangGraph + Ollama + React Leaflet | Hack Fusion 2025 | AI/ML Innovation Track</p>
      </footer>
    </div>
  );
}
