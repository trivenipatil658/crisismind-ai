import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.getenv("DATABASE_FILE", "crisismind.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            location TEXT,
            resource_data_json TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            total_capacity INTEGER,
            available_capacity INTEGER,
            food_available INTEGER DEFAULT 1,
            water_available INTEGER DEFAULT 1,
            medical_support INTEGER DEFAULT 0,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id TEXT PRIMARY KEY,
            disaster_type TEXT,
            location TEXT,
            recommended_path TEXT,
            recommended_route TEXT,
            final_score REAL,
            risk_level TEXT,
            success_probability REAL,
            full_result TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS route_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id TEXT,
            route_name TEXT,
            target_shelter TEXT,
            distance_km REAL,
            estimated_time_min INTEGER,
            route_status TEXT,
            required_resources_json TEXT,
            route_score REAL,
            selected INTEGER DEFAULT 0,
            explanation TEXT
        )
    """)
    conn.commit()
    conn.close()


# -- Resource functions --

def save_resource_update(role: str, location: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat() + "Z"
    # Delete old entry for same role+location, keep latest only
    conn.execute("DELETE FROM resources WHERE role=? AND location=?", (role, location))
    conn.execute(
        "INSERT INTO resources (role, location, resource_data_json, updated_at) VALUES (?,?,?,?)",
        (role, location, json.dumps(data), now)
    )
    conn.commit()
    conn.close()


def get_all_resources() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, location, resource_data_json, updated_at FROM resources ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [
        {"role": r[0], "location": r[1], "data": json.loads(r[2]), "updated_at": r[3]}
        for r in rows
    ]


def get_resources_dict() -> dict:
    """Return all resources grouped by role for agent consumption."""
    rows = get_all_resources()
    result = {}
    for r in rows:
        result[r["role"]] = {**r["data"], "location": r["location"], "updated_at": r["updated_at"]}
    return result


# -- Shelter functions --

def save_shelter(data: dict):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute("DELETE FROM shelters WHERE name=? AND location=?", (data["name"], data["location"]))
    conn.execute(
        "INSERT INTO shelters (name, location, latitude, longitude, total_capacity, available_capacity, "
        "food_available, water_available, medical_support, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            data["name"], data["location"], data["latitude"], data["longitude"],
            data["total_capacity"], data["available_capacity"],
            int(data.get("food_available", True)), int(data.get("water_available", True)),
            int(data.get("medical_support", False)), now
        )
    )
    conn.commit()
    conn.close()


def get_all_shelters() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM shelters ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [
        {
            "id": r[0], "name": r[1], "location": r[2], "latitude": r[3], "longitude": r[4],
            "total_capacity": r[5], "available_capacity": r[6],
            "food_available": bool(r[7]), "water_available": bool(r[8]),
            "medical_support": bool(r[9]), "updated_at": r[10]
        }
        for r in rows
    ]


# -- Simulation functions --

def save_simulation(sim_id: str, result: dict):
    best = next((p for p in result["decision_paths"] if p["path_id"] == result["recommended_path"]), {})
    best_route = result.get("recommended_route", "")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO simulations VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            sim_id,
            result["disaster_type"],
            result["location"],
            result["recommended_path"],
            best_route,
            best.get("final_decision_score", 0),
            result.get("risk_level", "Unknown"),
            best.get("success_probability", 0),
            json.dumps(result),
            result["created_at"],
        ),
    )
    # Save route recommendations
    for route in result.get("route_options", []):
        conn.execute(
            "INSERT INTO route_recommendations (simulation_id, route_name, target_shelter, distance_km, "
            "estimated_time_min, route_status, required_resources_json, route_score, selected, explanation) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                sim_id, route["route_name"], route["target_shelter"],
                route["distance_km"], route["estimated_time_min"], route["route_status"],
                json.dumps(route.get("required_resources", [])),
                route.get("route_score", 0),
                int(route.get("selected", False)),
                route.get("explanation", "")
            )
        )
    conn.commit()
    conn.close()


def get_all_simulations() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, disaster_type, location, recommended_path, recommended_route, "
        "final_score, risk_level, created_at FROM simulations ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [
        {
            "simulation_id": r[0], "disaster_type": r[1], "location": r[2],
            "recommended_path": r[3], "recommended_route": r[4],
            "final_score": r[5], "risk_level": r[6], "created_at": r[7],
        }
        for r in rows
    ]


def get_simulation_by_id(sim_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT full_result FROM simulations WHERE id=?", (sim_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None
