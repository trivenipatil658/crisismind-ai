const BASE = "http://127.0.0.1:8000";

export async function runSimulation(data) {
  const res = await fetch(`${BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateResources(data) {
  const res = await fetch(`${BASE}/resources/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateShelter(data) {
  const res = await fetch(`${BASE}/shelters/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchResources() {
  const res = await fetch(`${BASE}/resources`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchHistory() {
  const res = await fetch(`${BASE}/history`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchSimulation(id) {
  const res = await fetch(`${BASE}/simulation/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchLLMStatus() {
  const res = await fetch(`${BASE}/llm/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateReport(simulation_id) {
  const res = await fetch(`${BASE}/llm/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ simulation_id }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
