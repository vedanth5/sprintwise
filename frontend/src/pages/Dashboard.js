import React, { useEffect, useState, useCallback } from "react";
import { dashboardAPI, recommendationsAPI } from "../services/api";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, Tooltip, Legend, Title
} from "chart.js";
import Reveal from "../components/Reveal";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend, Title);

function RecommendationCard({ rec, onDismiss }) {
  const getIcon = (p) => p === "high" ? "🔴" : p === "medium" ? "🟡" : "🔵";
  
  return (
    <div className={`rec-card ${rec.priority}`}>
      <div style={{ flex: 1 }}>
        <div className="rec-title">
          <span>{getIcon(rec.priority)}</span>
          {rec.title}
        </div>
        <div className="rec-body">{rec.body}</div>
        <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className={`badge badge-${rec.priority}`} style={{ fontSize: 10 }}>{rec.priority.toUpperCase()}</span>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{rec.category}</span>
          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>✨ AI Insight</span>
        </div>
      </div>
      <div className="rec-dismiss" onClick={() => onDismiss(rec.rec_id)} title="Dismiss">
        ✕
      </div>
    </div>
  );
}

function StatCard({ title, value, sub, accent, icon }) {
  return (
    <div className={`card stat-card stat-${accent}`}>
      <div className="card-title">{icon} {title}</div>
      <div className="card-value">{value ?? "—"}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  );
}

export default function Dashboard({ navigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await dashboardAPI.getSummary();
      setData(res.data);
    } catch {
      setError("Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const dismiss = async (recId) => {
    await recommendationsAPI.dismiss(recId);
    load();
  };

  if (loading) return <div className="loading"><div className="loading-spinner" /><p>Loading dashboard...</p></div>;
  if (error) return <div className="page-body"><div className="alert alert-info">{error}</div></div>;

  const sprint = data?.active_sprint;
  const metrics = sprint?.metrics || {};
  const completionRate = metrics.completion_rate ?? 0;
  const subjects = metrics.subject_scores || {};
  const trend = data?.sprint_trend || [];
  const recs = data?.recommendations || [];
  const nextTask = data?.next_task_suggestion;

  // Trend chart data
  const trendChart = {
    labels: trend.map(s => s.name?.substring(0, 12) || "Sprint"),
    datasets: [{
      label: "Completion Rate (%)",
      data: trend.map(s => s.completion_rate || 0),
      backgroundColor: trend.map(s => s.completion_rate > 70 ? "#10B981" : s.completion_rate > 40 ? "#F59E0B" : "#EF4444"),
      borderRadius: 12,
      borderSkipped: false,
      barThickness: 20,
    }]
  };

  // Subject chart data
  const subjectNames = Object.keys(subjects);
  const subjectChart = {
    labels: subjectNames,
    datasets: [{
      data: subjectNames.map(s => subjects[s].score),
      backgroundColor: subjectNames.map((_, i) => {
        const colors = ["#8B5CF6", "#3B82F6", "#10B981", "#F59E0B", "#EF4444"];
        return colors[i % colors.length];
      }),
      borderColor: "#161618",
      borderWidth: 4,
    }]
  };

  const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: {
        backgroundColor: "#1E1E20",
        titleColor: "#FFF",
        bodyColor: "#A1A1AA",
        padding: 12,
        cornerRadius: 8,
        displayColors: false
      }
    },
    scales: { 
      y: { 
        beginAtZero: true, max: 100, 
        grid: { color: "rgba(255,255,255,0.05)" }, 
        ticks: { color: "#52525B", font: { size: 10, weight: "600" } } 
      }, 
      x: { 
        grid: { display: false }, 
        ticks: { color: "#52525B", font: { size: 10, weight: "600" } } 
      } 
    }
  };

  const doughnutOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { 
      legend: { position: "right", labels: { color: "#A1A1AA", font: { size: 11 }, boxWidth: 8, padding: 15 } },
      tooltip: {
        backgroundColor: "#1E1E20",
        padding: 12,
        cornerRadius: 8
      }
    },
    cutout: "75%"
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Your academic health at a glance</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {data?.study_streak_days > 0 && (
            <div className="streak-badge">🔥 {data.study_streak_days}-day streak</div>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => navigate("sprints")}>+ New Sprint</button>
        </div>
      </div>

      <div className="page-body">
        {/* Stat cards */}
        <div className="grid-4" style={{ marginBottom: 24 }}>
          <Reveal delay={100} width="100%">
            <StatCard icon="✅" title="Completion Rate" value={sprint ? `${completionRate.toFixed(0)}%` : "—"} sub={sprint?.name || "No active sprint"} accent="blue" />
          </Reveal>
          <Reveal delay={200} width="100%">
            <StatCard icon="📅" title="Consistency" value={metrics.consistency_index != null ? `${(metrics.consistency_index * 100).toFixed(0)}%` : "—"} sub="Study days / sprint days" accent="green" />
          </Reveal>
          <Reveal delay={300} width="100%">
            <StatCard icon="⏱️" title="Hours This Week" value={`${data?.total_study_hours_week ?? 0}h`} sub="Logged via time tracker" accent="purple" />
          </Reveal>
          <Reveal delay={400} width="100%">
            <StatCard icon="🏁" title="Total Sprints" value={data?.stats?.total_sprints ?? 0} sub={`${data?.stats?.total_tasks_completed ?? 0} tasks completed`} accent="orange" />
          </Reveal>
        </div>

        {/* AI Recommendations */}
        {recs.length > 0 && (
          <Reveal delay={500} width="100%">
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="section-header">
                <div className="section-title">🤖 AI Recommendations</div>
                <span style={{ fontSize: 12, color: "var(--gray-400)" }}>{recs.length} active</span>
              </div>
              {recs.map(r => <RecommendationCard key={r.rec_id} rec={r} onDismiss={dismiss} />)}
            </div>
          </Reveal>
        )}

        {/* Next task suggestion */}
        {nextTask && (
          <Reveal delay={600} width="100%">
            <div className="next-task-box" style={{ marginBottom: 24 }}>
              <div className="next-task-icon">🎯</div>
              <div style={{ flex: 1 }}>
                <div className="next-task-label">Suggested Next Task</div>
                <div className="next-task-desc">{nextTask.description}</div>
                <div className="next-task-reason">
                  <span className="task-subject">{nextTask.subject}</span>
                  <span style={{ marginLeft: 8 }}>{nextTask.suggestion_reason}</span>
                </div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => navigate("sprint-detail", { sprintId: sprint?.sprint_id })}>
                View Sprint →
              </button>
            </div>
          </Reveal>
        )}

        {/* Charts row */}
        <div className="grid-2" style={{ marginBottom: 24 }}>
          <Reveal delay={700} width="100%">
            <div className="card">
              <div className="section-title" style={{ marginBottom: 12 }}>📈 Sprint Completion Trend</div>
              <div className="chart-wrap">
                {trend.length > 0
                  ? <Bar data={trendChart} options={chartOpts} />
                  : <div className="empty-state"><div className="empty-icon">📊</div><div className="empty-text">Complete sprints to see your trend</div></div>
                }
              </div>
            </div>
          </Reveal>

          <Reveal delay={800} width="100%">
            <div className="card">
              <div className="section-title" style={{ marginBottom: 12 }}>📚 Subject Performance</div>
              <div className="chart-wrap">
                {subjectNames.length > 0
                  ? <Doughnut data={subjectChart} options={doughnutOpts} />
                  : <div className="empty-state"><div className="empty-icon">📚</div><div className="empty-text">Add tasks with subject tags to see breakdown</div></div>
                }
              </div>
            </div>
          </Reveal>
        </div>

        {/* Active sprint progress */}
        {sprint ? (
          <div className="card">
            <div className="section-header">
              <div className="section-title">🏃 Active Sprint: {sprint.name}</div>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate("sprint-detail", { sprintId: sprint.sprint_id })}>View Details →</button>
            </div>
            <div style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, color: "var(--gray-500)" }}>Overall Progress</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{completionRate.toFixed(0)}%</span>
              </div>
              <div className="progress-bar-wrap">
                <div
                  className={`progress-bar-fill ${completionRate >= 70 ? "progress-green" : completionRate >= 40 ? "progress-blue" : "progress-red"}`}
                  style={{ width: `${completionRate}%` }}
                />
              </div>
            </div>
            {/* Subject sub-progress */}
            {subjectNames.slice(0, 4).map(subject => (
              <div key={subject} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: "var(--gray-600)" }}>{subject}</span>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>
                    {subjects[subject].completed}/{subjects[subject].total}
                    <span className={`badge badge-${subjects[subject].classification}`} style={{ marginLeft: 6 }}>{subjects[subject].classification}</span>
                  </span>
                </div>
                <div className="progress-bar-wrap" style={{ height: 5 }}>
                  <div
                    className={`progress-bar-fill ${subjects[subject].score >= 75 ? "progress-green" : subjects[subject].score >= 50 ? "progress-blue" : "progress-red"}`}
                    style={{ width: `${subjects[subject].score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card">
            <div className="empty-state">
              <div className="empty-icon">🚀</div>
              <div className="empty-title">No Active Sprint</div>
              <div className="empty-text">Create a sprint to start tracking your academic progress with AI guidance.</div>
              <button className="btn btn-primary" onClick={() => navigate("sprints")}>Create Your First Sprint</button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
