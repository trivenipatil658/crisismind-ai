import { useState } from "react";
import "leaflet/dist/leaflet.css";
import "./styles.css";

import Crisis3DScene from "./components/Crisis3DScene";
import { useAuth, ROLE_ICONS } from "./AuthContext";

import LoginPage from "./components/LoginPage";
import LLMStatus from "./components/LLMStatus";
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
import WhatIfPanel from "./components/WhatIfPanel";
import HumanApproval from "./components/HumanApproval";
import ScoreBreakdown from "./components/ScoreBreakdown";
import ResourceFreshness from "./components/ResourceFreshness";

import { runSimulation, updateResources } from "./api";
import { DEMO_RESOURCES } from "./demo";

import RiskRadar3D from "./components/RiskRadar3D";
import ResourceControl3D from "./components/ResourceControl3D";
import WeatherContextCard from "./components/WeatherContextCard";
import NotificationCenter from "./components/NotificationCenter";

export default function App() {
  const { user, logout } = useAuth();

  const [result, setResult] = useState(null);
  const [lastInput, setLastInput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState(null);

  // If user is not logged in, show login page
  if (!user) {
    return <LoginPage />;
  }

  const isAdmin = user.role === "Crisis Admin";

  const handleSimulate = async (data) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setLastInput(data);

    try {
      const simulationResult = await runSimulation(data);
      setResult(simulationResult);
    } catch (err) {
      setError(err?.message || "Simulation failed. Please check backend server.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemoResources = async () => {
    setDemoLoading(true);
    setError(null);

    try {
      for (const resourceData of Object.values(DEMO_RESOURCES)) {
        await updateResources(resourceData);
      }

      alert("Demo resources loaded for all roles. Now run the simulation.");
    } catch (err) {
      setError(err?.message || "Failed to load demo resources.");
    } finally {
      setDemoLoading(false);
    }
  };

  const handleLoadHistory = (simulation) => {
    setResult(simulation);
    setError(null);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <div className="app">
      {/* ================= HEADER ================= */}
      <header className="header">
        <div className="header-content">
          <h1 className="title">CrisisMind AI</h1>

          <p className="subtitle">
            Role-Based LangGraph Disaster Response and Route Decision Simulator
          </p>

          <p className="tagline">
            Simulate disaster. Track resources. Compare actions. Visualize routes.
            Choose the safest response.
          </p>

          <div className="header-status-row">
            <LLMStatus />

            <div className="auth-bar">
              <span className="auth-role-pill">
                <span className="auth-role-icon">{ROLE_ICONS[user.role]}</span>
                <strong>{user.role}</strong>
                {isAdmin && <span className="auth-admin-tag">ADMIN</span>}
              </span>

              <button className="auth-logout-btn" onClick={logout}>
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* ================= MAIN CONTENT ================= */}
      <main className="main">
        {/* Professional animated 3D command center visual */}
        <Crisis3DScene />

        {/* Resource Control Board - always visible */}
        <ResourceControl3D />

        {/* ================= ROLE OFFICER VIEW ================= */}
        {!isAdmin && (
          <>
            <div className="role-restricted-banner">
              <span>
                🔒 You are logged in as <strong>{user.role}</strong>. You can
                update only your department resource information.
              </span>
            </div>

            <ResourceDashboard role={user.role} />
          </>
        )}

        {/* ================= ADMIN VIEW ================= */}
        {isAdmin && (
          <>
            <section className="card demo-resources-card">
              <div className="admin-setup-header">
                <div>
                  <h2 className="section-title">Quick Setup</h2>
                  <p className="muted admin-setup-text">
                    Load demo resource data for all roles before running the
                    simulation, or ask each role officer to submit their updates.
                  </p>
                </div>

                <button
                  className="btn-secondary"
                  onClick={handleLoadDemoResources}
                  disabled={demoLoading}
                >
                  {demoLoading
                    ? "Loading resources..."
                    : "Load Demo Resources"}
                </button>
              </div>
            </section>

            <CrisisForm onSubmit={handleSimulate} loading={loading} />
          </>
        )}

        {/* ================= ERROR MESSAGE ================= */}
        {error && (
          <div className="card error-card">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ================= SIMULATION RESULTS ================= */}
        {isAdmin && result && (
          <section className="results-section">
            <RecommendationCard result={result} />

            <RiskRadar3D result={result} />

            {result.weather_context && (
              <WeatherContextCard weather={result.weather_context} />
            )}

            <ResourceFreshness />

            <RouteMap
              lat={result.latitude}
              lng={result.longitude}
              routes={result.route_options}
              recommended={result.recommended_route}
              disasterType={result.disaster_type}
              location={result.location}
              affectedPopulation={result.affected_population || 20000}
            />

            <RouteRecommendation
              routes={result.route_options}
              recommended={result.recommended_route}
            />

            <WorkflowTrace trace={result.workflow_trace} />

            <DecisionComparison
              paths={result.decision_paths}
              recommended={result.recommended_path}
            />

            <ScoreBreakdown simulationId={result.simulation_id} />

            <AgentSuggestions suggestions={result.agent_suggestions} />

            <ExplainabilityBox
              explanation={result.explanation}
              scenarios={result.generated_scenarios}
              llmUsed={result.llm_used}
            />

            {lastInput && (
              <WhatIfPanel
                originalInput={lastInput}
                simulationId={result.simulation_id}
              />
            )}

            <HumanApproval
              simulationId={result.simulation_id}
              recommendedPath={result.recommended_path}
              recommendedRoute={result.recommended_route}
            />

            <NotificationCenter
              simulationId={result.simulation_id}
              approved={result.approved}
            />

            <AIReport
              simulationId={result.simulation_id}
              llmUsed={result.llm_used}
            />

            <div className="card scenario-card">
              <h2 className="section-title">Scenario Summary</h2>
              <p>{result.scenario_summary}</p>
            </div>
          </section>
        )}

        {/* ================= HISTORY ================= */}
        {isAdmin && <History onLoad={handleLoadHistory} />}
      </main>

      {/* ================= FOOTER ================= */}
      <footer className="footer">
        <p>
          CrisisMind AI | FastAPI + LangGraph + Ollama + React Leaflet | Hack
          Fusion 2025 | AI/ML Innovation Track
        </p>
      </footer>
    </div>
  );
}