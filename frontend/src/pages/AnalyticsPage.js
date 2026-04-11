import React, { useEffect, useState } from "react";
import { analyticsAPI } from "../services/api";
import { Line, Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler } from "chart.js";
import Reveal from "../components/Reveal";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler);

export default function AnalyticsPage() {
  const [history, setHistory] = useState([]);
  const [anomaly, setAnomaly] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsAPI.getHistory(), analyticsAPI.getAnomaly()])
      .then(([hRes, aRes]) => {
        setHistory(hRes.data.history.reverse());
        setAnomaly(aRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="loading-spinner" /></div>;

  const labels = history.map(h => h.sprint_name?.substring(0, 12) || "Sprint");

  const completionData = {
    labels,
    datasets: [{
      label: "Completion Rate (%)",
      data: history.map(h => h.completion_rate ?? 0),
      borderColor: "#8B5CF6",
      backgroundColor: "rgba(139, 92, 246, 0.08)",
      tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 6,
    }]
  };

  const consistencyData = {
    labels,
    datasets: [{
      label: "Consistency Index",
      data: history.map(h => ((h.consistency_index ?? 0) * 100).toFixed(1)),
      backgroundColor: history.map(h => (h.consistency_index ?? 0) >= 0.7 ? "#10B981" : (h.consistency_index ?? 0) >= 0.4 ? "#F59E0B" : "#EF4444"),
      borderRadius: 12, borderSkipped: false,
    }]
  };

  const hoursData = {
    labels,
    datasets: [{
      label: "Study Hours",
      data: history.map(h => h.total_study_hours ?? 0),
      backgroundColor: "#3B82F6",
      borderRadius: 12, borderSkipped: false,
    }]
  };

  const lineOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: { backgroundColor: "#1E1E20", padding: 12, cornerRadius: 8 }
    },
    scales: { 
      y: { beginAtZero: true, max: 100, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#52525B", font: { size: 10 } } }, 
      x: { grid: { display: false }, ticks: { color: "#52525B", font: { size: 10 } } } 
    }
  };
  const barOpts = { ...lineOpts, scales: { ...lineOpts.scales, y: { beginAtZero: true, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#52525B", font: { size: 10 } } } } };

  // Sprint history table data
  const avgCompletion = history.length ? (history.reduce((s, h) => s + (h.completion_rate ?? 0), 0) / history.length).toFixed(1) : 0;
  const avgConsistency = history.length ? ((history.reduce((s, h) => s + (h.consistency_index ?? 0), 0) / history.length) * 100).toFixed(1) : 0;
  const totalHours = history.reduce((s, h) => s + (h.total_study_hours ?? 0), 0).toFixed(1);

  return (
    <>
      <div className="page-header">
        <div><h2>Analytics</h2><p>Performance history across all sprints</p></div>
      </div>
      <div className="page-body">

        {/* Anomaly alert */}
        {anomaly?.is_anomalous && (
          <div className="card" style={{ marginBottom: 24, borderLeft: "4px solid var(--red)", background: "var(--red-bg)" }}>
            <div style={{ color: "var(--red)", fontWeight: 600, fontSize: 14 }}>
              ⚠️ Performance Anomaly Detected
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
              Your most recent sprint ({anomaly.most_recent_rate?.toFixed(0)}%) is significantly below your personal average ({anomaly.historical_mean?.toFixed(0)}%). Z-score: {anomaly.z_score?.toFixed(2)}.
            </div>
          </div>
        )}

        {history.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <div className="empty-title">No Sprint History Yet</div>
            <div className="empty-text">Complete your first sprint to unlock analytics and performance trends.</div>
          </div>
        ) : (
          <>
            {/* Summary cards */}
            <div className="grid-3" style={{ marginBottom: 24 }}>
              {[
                { label: "Avg Completion Rate", value: `${avgCompletion}%`, icon: "✅", accent: "blue" },
                { label: "Avg Consistency", value: `${avgConsistency}%`, icon: "📅", accent: "green" },
                { label: "Total Study Hours", value: `${totalHours}h`, icon: "⏱️", accent: "purple" },
              ].map(({ label, value, icon, accent }, index) => (
                <Reveal key={label} delay={index * 100} width="100%">
                  <div className={`card stat-card stat-${accent}`}>
                    <div className="card-title">{icon} {label}</div>
                    <div className="card-value">{value}</div>
                    <div className="card-sub">Across {history.length} sprints</div>
                  </div>
                </Reveal>
              ))}
            </div>

            {/* Completion trend chart */}
            <Reveal delay={400} width="100%">
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="section-title" style={{ marginBottom: 12 }}>📈 Completion Rate Trend</div>
                <div className="chart-wrap"><Line data={completionData} options={lineOpts} /></div>
              </div>
            </Reveal>

            <div className="grid-2" style={{ marginBottom: 20 }}>
              <Reveal delay={500} width="100%">
                <div className="card">
                  <div className="section-title" style={{ marginBottom: 12 }}>📅 Study Consistency</div>
                  <div className="chart-wrap"><Bar data={consistencyData} options={barOpts} /></div>
                </div>
              </Reveal>
              <Reveal delay={600} width="100%">
                <div className="card">
                  <div className="section-title" style={{ marginBottom: 12 }}>⏱️ Total Study Hours per Sprint</div>
                  <div className="chart-wrap"><Bar data={hoursData} options={barOpts} /></div>
                </div>
              </Reveal>
            </div>

            {/* Sprint history table */}
            <Reveal delay={700} width="100%">
              <div className="card">
                <div className="section-title" style={{ marginBottom: 16 }}>📋 Sprint History</div>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr style={{ background: "var(--gray-50)", borderBottom: "2px solid var(--gray-200)" }}>
                        {["Sprint", "Dates", "Status", "Completion", "Consistency", "Hours"].map(h => (
                          <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "var(--gray-600)", fontSize: 12 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[...history].reverse().map((h, i) => (
                        <tr key={h.sprint_id} style={{ borderBottom: "1px solid var(--gray-100)", background: i % 2 === 0 ? "var(--white)" : "var(--gray-50)" }}>
                          <td style={{ padding: "10px 14px", fontWeight: 500 }}>{h.sprint_name}</td>
                          <td style={{ padding: "10px 14px", color: "var(--gray-500)" }}>{h.start_date} → {h.end_date}</td>
                          <td style={{ padding: "10px 14px" }}>
                            <span className={`badge badge-${h.status === "active" ? "in_progress" : "completed"}`}>{h.status}</span>
                          </td>
                          <td style={{ padding: "10px 14px" }}>
                            <span style={{ fontWeight: 600, color: (h.completion_rate ?? 0) >= 70 ? "var(--green)" : (h.completion_rate ?? 0) >= 40 ? "#C05621" : "var(--red)" }}>
                              {h.completion_rate?.toFixed(0) ?? "—"}%
                            </span>
                          </td>
                          <td style={{ padding: "10px 14px" }}>{h.consistency_index != null ? `${(h.consistency_index * 100).toFixed(0)}%` : "—"}</td>
                          <td style={{ padding: "10px 14px" }}>{h.total_study_hours?.toFixed(1) ?? "0"}h</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Reveal>
          </>
        )}
      </div>
    </>
  );
}
