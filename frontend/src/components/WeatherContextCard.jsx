import React from "react";

const WeatherContextCard = ({ weather }) => {
  if (!weather) return null;

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case "low":
        return "weather-rag-risk-low";
      case "medium":
        return "weather-rag-risk-medium";
      case "high":
        return "weather-rag-risk-high";
      case "critical":
        return "weather-rag-risk-critical";
      default:
        return "weather-rag-risk-low";
    }
  };

  return (
    <div className="card weather-rag-card">
      <div className="weather-rag-header">
        <h2 className="section-title weather-rag-title">
          Live Weather Context
          <span className="weather-rag-badge">Vectorless RAG</span>
        </h2>
      </div>

      <div className="weather-rag-grid">
        <div className="weather-rag-item">
          <span className="weather-rag-label">Condition:</span>
          <span className="weather-rag-value">{weather.condition}</span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Rainfall:</span>
          <span className="weather-rag-value">{weather.rainfall_mm} mm</span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Wind Speed:</span>
          <span className="weather-rag-value">{weather.wind_speed_kmph} km/h</span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Humidity:</span>
          <span className="weather-rag-value">{weather.humidity_percent}%</span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Visibility:</span>
          <span className="weather-rag-value">{weather.visibility_km} km</span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Risk Level:</span>
          <span className={`weather-rag-value ${getRiskColor(weather.risk_level)}`}>
            {weather.risk_level}
          </span>
        </div>
        <div className="weather-rag-item">
          <span className="weather-rag-label">Retrieved:</span>
          <span className="weather-rag-value">
            {new Date(weather.retrieved_at).toLocaleString()}
          </span>
        </div>
      </div>

      <div className="weather-rag-note">
        <strong>Risk Note:</strong> {weather.risk_note}
      </div>
    </div>
  );
};

export default WeatherContextCard;