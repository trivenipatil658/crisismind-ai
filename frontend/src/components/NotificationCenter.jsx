import { useState, useEffect } from "react";
import { previewNotifications, sendNotifications } from "../api";

export default function NotificationCenter({ simulationId, approved }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [alertTarget, setAlertTarget] = useState("both");
  const [region, setRegion] = useState("Zone A");
  const [approvedBy, setApprovedBy] = useState("Crisis Admin");
  const [sendResult, setSendResult] = useState(null);

  const handlePreview = async () => {
    if (!simulationId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await previewNotifications(simulationId, alertTarget, region);
      setPreview(result);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleSend = async () => {
    if (!simulationId || !approved) return;
    setLoading(true);
    setError(null);
    try {
      const result = await sendNotifications(simulationId, alertTarget, region, approvedBy);
      setSendResult(result);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (simulationId && approved) {
      handlePreview();
    }
  }, [simulationId, approved, alertTarget, region]);

  if (!simulationId) {
    return (
      <div className="card notification-card">
        <h2 className="section-title">📢 Emergency Notification Center</h2>
        <p className="muted">Run a simulation and get it approved to send emergency alerts.</p>
      </div>
    );
  }

  if (!approved) {
    return (
      <div className="card notification-card">
        <h2 className="section-title">📢 Emergency Notification Center</h2>
        <div className="notification-warning">
          ⚠️ <strong>Approval Required:</strong> Simulation must be approved by Crisis Admin before sending notifications.
        </div>
      </div>
    );
  }

  return (
    <div className="card notification-card">
      <h2 className="section-title">📢 Emergency Notification Center</h2>
      <p className="muted" style={{ marginBottom: "16px" }}>
        Send SMS alerts to emergency teams and affected public. All alerts require human approval.
      </p>

      <div className="notification-controls">
        <div className="control-row">
          <label>
            Alert Target
            <select value={alertTarget} onChange={e => setAlertTarget(e.target.value)}>
              <option value="both">Both Teams & Public</option>
              <option value="team">Emergency Teams Only</option>
              <option value="public">Public Only</option>
            </select>
          </label>
          <label>
            Region
            <select value={region} onChange={e => setRegion(e.target.value)}>
              <option value="Zone A">Zone A</option>
              <option value="Zone B">Zone B</option>
              <option value="Zone C">Zone C</option>
            </select>
          </label>
          <label>
            Approved By
            <input
              value={approvedBy}
              onChange={e => setApprovedBy(e.target.value)}
              placeholder="Crisis Admin"
            />
          </label>
        </div>

        <div className="btn-row" style={{ marginTop: "12px" }}>
          <button className="btn-preview" onClick={handlePreview} disabled={loading}>
            {loading ? "⏳ Loading..." : "👁️ Preview Alerts"}
          </button>
          <button className="btn-send" onClick={handleSend} disabled={loading || !approved}>
            {loading ? "⏳ Sending..." : "📤 Send Alerts"}
          </button>
        </div>
      </div>

      {error && <div className="status-msg status-error">{error}</div>}

      {preview && (
        <div className="notification-preview">
          <h3 className="sub-title">📋 Alert Preview</h3>

          {preview.preview.team_alert && (
            <div className="alert-preview-box team-alert">
              <div className="alert-header">
                <span className="alert-type">🚨 TEAM ALERT</span>
                <span className="recipient-count">
                  📱 {preview.preview.team_alert.recipient_count} recipients
                </span>
              </div>
              <div className="alert-message">
                {preview.preview.team_alert.message}
              </div>
              <div className="recipient-list">
                <strong>Recipients:</strong>
                <div className="recipients">
                  {preview.preview.team_alert.recipients.map((r, i) => (
                    <span key={i} className="recipient-tag">
                      {r.name} ({r.role})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {preview.preview.public_alert && (
            <div className="alert-preview-box public-alert">
              <div className="alert-header">
                <span className="alert-type">📢 PUBLIC ALERT</span>
                <span className="recipient-count">
                  📱 {preview.preview.public_alert.recipient_count} recipients
                </span>
              </div>
              <div className="alert-message">
                {preview.preview.public_alert.message}
              </div>
              <div className="recipient-list">
                <strong>Recipients:</strong>
                <div className="recipients">
                  {preview.preview.public_alert.recipients.map((r, i) => (
                    <span key={i} className="recipient-tag">
                      {r.name} ({r.role})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {sendResult && (
        <div className="notification-result">
          <h3 className="sub-title">✅ Alerts Sent Successfully</h3>
          <div className="send-summary">
            <div className="summary-item">
              <strong>Mode:</strong> {sendResult.result.mode}
            </div>
            <div className="summary-item">
              <strong>Region:</strong> {sendResult.result.region}
            </div>
            <div className="summary-item">
              <strong>Approved By:</strong> {sendResult.result.approved_by}
            </div>
            <div className="summary-item">
              <strong>Sent At:</strong> {new Date(sendResult.result.created_at).toLocaleString()}
            </div>
          </div>

          {sendResult.result.team_alert && (
            <div className="alert-result">
              <h4>🚨 Team Alert Result</h4>
              <div className="result-details">
                <span className={`status-${sendResult.result.team_alert.status}`}>
                  Status: {sendResult.result.team_alert.status}
                </span>
                <span>Sent: {sendResult.result.team_alert.sent_count}</span>
                <span>Failed: {sendResult.result.team_alert.failed_count}</span>
              </div>
              <p className="provider-response">{sendResult.result.team_alert.provider_response}</p>
            </div>
          )}

          {sendResult.result.public_alert && (
            <div className="alert-result">
              <h4>📢 Public Alert Result</h4>
              <div className="result-details">
                <span className={`status-${sendResult.result.public_alert.status}`}>
                  Status: {sendResult.result.public_alert.status}
                </span>
                <span>Sent: {sendResult.result.public_alert.sent_count}</span>
                <span>Failed: {sendResult.result.public_alert.failed_count}</span>
              </div>
              <p className="provider-response">{sendResult.result.public_alert.provider_response}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}