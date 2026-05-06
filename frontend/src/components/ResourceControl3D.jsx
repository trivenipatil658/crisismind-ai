const FALLBACK = [
  { label: "Rescue Teams", value: 12, total: 15, status: "warning", icon: "🚑" },
  { label: "Hospital Beds", value: 500, total: 700, status: "warning", icon: "🏥" },
  { label: "Boats", value: 8, total: 10, status: "good", icon: "🚤" },
  { label: "Life Jackets", value: 120, total: 150, status: "good", icon: "🦺" },
  { label: "Shelter Capacity", value: 1130, total: 1600, status: "good", icon: "🏠" },
  { label: "Food Packets", value: 900, total: 1200, status: "good", icon: "🍱" },
  { label: "Ambulances", value: 4, total: 8, status: "critical", icon: "🚑" },
  { label: "Volunteers", value: 60, total: 80, status: "good", icon: "🤝" },
];

const STATUS_META = {
  good: { color: "#15803d", bg: "#ecfdf3", border: "#bbf7d0", label: "Good" },
  warning: { color: "#d97706", bg: "#fff7ed", border: "#fed7aa", label: "Warning" },
  critical: { color: "#dc2626", bg: "#fef2f2", border: "#fecaca", label: "Critical" },
};

export default function ResourceControl3D({ resources }) {
  const list = Array.isArray(resources) && resources.length ? resources : FALLBACK;

  return (
    <div className="resource3d-card card">
      <div className="resource3d-header">
        <span className="resource3d-title">📊 3D Resource Control Board</span>
        <p className="resource3d-subtitle">
          Shows operational readiness from role-based resource updates.
        </p>
      </div>

      <div className="resource3d-grid">
        {list.map((item) => {
          const sm = STATUS_META[item.status] || STATUS_META.good;
          const pct = item.total > 0 ? Math.round((item.value / item.total) * 100) : 0;

          return (
            <div
              key={item.label}
              className="resource3d-tile"
              style={{
                borderColor: sm.border,
                background: `linear-gradient(180deg, #ffffff 0%, ${sm.bg} 100%)`,
              }}
            >
              <div className="resource3d-tile-top">
                <span className="resource3d-icon" style={{ background: sm.color, color: "#fff" }}>
                  {item.icon}
                </span>
                <span
                  className="resource3d-status-badge"
                  style={{ background: sm.bg, color: sm.color, border: `1px solid ${sm.border}` }}
                >
                  {sm.label}
                </span>
              </div>

              <div className="resource3d-label">{item.label}</div>

              <div className="resource3d-numbers">
                <span className="resource3d-value">{item.value.toLocaleString()}</span>
                <span className="resource3d-total">/ {item.total.toLocaleString()}</span>
              </div>

              <div className="resource3d-bar-bg">
                <div
                  className="resource3d-bar-fill"
                  style={{ width: `${pct}%`, background: sm.color }}
                />
              </div>
              <div className="resource3d-pct">{pct}% available</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
