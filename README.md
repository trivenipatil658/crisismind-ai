# CrisisMind AI 🚨

## CrisisMind AI — Current Project Overview

CrisisMind AI is a full-stack disaster response simulation platform built in the `trivenipatil658/crisismind-ai` repository.

It combines a Python/FastAPI backend with a React/Vite frontend to simulate weather-aware disaster response decisions, resource planning, and explainable agent recommendations.

---

## What This Project Does

- Runs a **LangGraph-based disaster decision workflow** with structured expert agents
- Retrieves **weather-aware context** via a vectorless RAG-style weather retriever
- Scores and compares response paths with **weather-adjusted risk, route safety, and feasibility**
- Displays results in a **professional command center dashboard**
- Saves simulation history and supports **human approval / notification preview**

This version is updated to reflect the current working project state, including the latest frontend dashboard and backend service architecture.

---

## Key Features

- **Weather-aware disaster simulation**: flood, fire, earthquake, and other scenarios
- **LangGraph expert workflow**: multiple agent nodes run in sequence to produce decisions
- **Explainable AI**: each recommendation includes justifications and risk reasoning
- **Resource control board**: real-time availability, status badges, and progress bars
- **Route recommendation and map visualization**
- **Workflow execution trace** for transparency
- **Agent suggestions** and explainability panel
- **Human approval flow** with notification preview
- **Offline-capable demo mode** using fallback weather logic
- **Docker support** for backend + frontend deployment

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLite
- **Frontend**: React, Vite, JavaScript, Leaflet
- **AI Orchestration**: LangGraph-based workflow with deterministic agents
- **Weather Context**: Vectorless RAG-style retrieval logic
- **Deployment**: Docker Compose

---

## Repository Structure

```
crisismind-ai/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── schemas.py
│   ├── simulator.py
│   ├── scoring.py
│   ├── langgraph_workflow.py
│   ├── graph_state.py
│   ├── agents.py
│   ├── route_planner.py
│   ├── llm_service.py
│   ├── services/
│   │   ├── sms_service.py
│   │   └── email_service.py
│   ├── tools/
│   │   └── weather_retriever.py
│   ├── requirements.txt
│   └── data/
│       └── crisismind.db
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── styles.css
│   │   ├── demo.js
│   │   ├── components/
│   │   │   ├── Crisis3DScene.jsx
│   │   │   ├── ResourceControl3D.jsx
│   │   │   ├── RiskRadar3D.jsx
│   │   │   ├── RouteRecommendation.jsx
│   │   │   ├── RouteMap.jsx
│   │   │   ├── WorkflowTrace.jsx
│   │   │   ├── AgentSuggestions.jsx
│   │   │   ├── ExplainabilityBox.jsx
│   │   │   ├── NotificationCenter.jsx
│   │   │   └── ...
│   └── public/
└── docker-compose.yml
```

---

## Current UI Features

- **3D Crisis Command Scene** with animated visualization
- **Resource Control Board** with status tiles and progress bars
- **Risk Radar 3D** for threat and readiness overview
- **Route Map** and **Route Recommendation** panels
- **Workflow Trace** showing decision execution steps
- **Agent Suggestions** and explainability cards
- **Weather Context Card** displaying current weather and risk
- **History and Human Approval** for audit and notifications

---

## Current Backend Flow

1. Receive simulation input
2. Retrieve weather context using disaster type and location
3. Build LangGraph workflow state
4. Execute agent nodes for resource, rescue, transport, safety, and scoring
5. Generate recommended path and route
6. Save simulation result to SQLite
7. Return a rich response including weather context, decision trace, and explanations

---

## API Endpoints

- `GET /` — Health check
- `POST /simulate` — Run a full simulation
- `GET /history` — Retrieve all saved simulations
- `GET /simulation/{simulation_id}` — Get one simulation result
- `GET /llm/status` — Check LLM availability and mode
- `POST /resources/update` — Save resource updates
- `POST /shelters/update` — Save shelter updates
- `GET /resources` — Fetch current resources and shelters

---

## Running the Project Locally

### Backend

```bash
cd backend
python -m venv .venv
# PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker (Backend + Frontend)

```bash
docker compose up --build
```

### Default URLs

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

---

## Demo Steps

1. Start backend and frontend
2. Log in as admin
3. Load demo resources or update resource values
4. Enter disaster scenario details
5. Run the simulation
6. Review dashboard results, weather context, and recommended response

---

## Notes

- The app supports **LLM-enhanced** execution when Ollama is available
- Weather context is used to adjust risk, route safety, and confidence
- The frontend is a modern React dashboard with a clean UI
- The backend can run locally or via Docker Compose

---

## GitHub Repository

- `https://github.com/trivenipatil658/crisismind-ai`

*Updated to reflect the current project state on May 6, 2026.*
