import React, { useEffect, useState, useCallback, useRef } from "react";
import { sprintsAPI, tasksAPI, timelogsAPI, analyticsAPI } from "../services/api";

function AddTaskModal({ sprintId, onClose, onAdded }) {
  const [form, setForm] = useState({ subject: "", description: "", estimated_minutes: 30, priority: "medium" });
  const [error, setError] = useState("");
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));
  const submit = async (e) => {
    e.preventDefault();
    try {
      const res = await tasksAPI.create({ ...form, sprint_id: sprintId, estimated_minutes: parseInt(form.estimated_minutes) });
      onAdded(res.data.task);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create task");
    }
  };
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">➕ Add Task</div>
          <span className="modal-close" onClick={onClose}>✕</span>
        </div>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Subject</label>
            <input className="form-input" placeholder="e.g. Mathematics" value={form.subject} onChange={set("subject")} required />
          </div>
          <div className="form-group">
            <label className="form-label">Task Description</label>
            <input className="form-input" placeholder="e.g. Solve integration problems – Chapter 5" value={form.description} onChange={set("description")} required />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Estimated Time (minutes)</label>
              <input className="form-input" type="number" min="5" max="480" value={form.estimated_minutes} onChange={set("estimated_minutes")} />
            </div>
            <div className="form-group">
              <label className="form-label">Priority</label>
              <select className="form-select" value={form.priority} onChange={set("priority")}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">Add Task</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TaskCard({ task, onUpdate, onDelete }) {
  const [activeLog, setActiveLog] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef(null);

  const startTimer = async () => {
    const res = await timelogsAPI.start(task.task_id);
    setActiveLog(res.data.log);
    setElapsed(0);
  };
  const stopTimer = async () => {
    if (!activeLog) return;
    await timelogsAPI.stop(activeLog.log_id, task.task_id);
    clearInterval(timerRef.current);
    setActiveLog(null);
    setElapsed(0);
    onUpdate(task.task_id, {});
  };

  useEffect(() => {
    if (activeLog) {
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [activeLog]);

  const toggleDone = () => onUpdate(task.task_id, { status: task.status === "completed" ? "pending" : "completed" });

  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  const totalMins = Math.round((task.total_time_spent_seconds || 0) / 60);

  return (
    <div className={`task-card ${task.status === "completed" ? "completed" : ""}`}>
      <div className={`task-check ${task.status === "completed" ? "done" : ""}`} onClick={toggleDone}>
        {task.status === "completed" && "✓"}
      </div>
      <div className="task-info">
        <div className={`task-desc ${task.status === "completed" ? "done" : ""}`}>{task.description}</div>
        <div className="task-meta">
          <span className="task-subject">{task.subject}</span>
          <span className={`badge badge-${task.priority}`}>{task.priority}</span>
          <span className="task-time">Est: {task.estimated_minutes}m</span>
          {totalMins > 0 && <span className="task-time" style={{ color: "var(--blue)" }}>Logged: {totalMins}m</span>}
          {activeLog && <span style={{ fontSize: 11, color: "var(--red)", fontWeight: 600 }}>⏱ {fmt(elapsed)}</span>}
        </div>
      </div>
      <div className="task-actions">
        {task.status !== "completed" && (
          activeLog
            ? <button className="task-timer-btn stop" onClick={stopTimer}>⏹ Stop</button>
            : <button className="task-timer-btn start" onClick={startTimer}>▶ Start</button>
        )}
        <button className="btn btn-danger btn-sm" onClick={() => onDelete(task.task_id)}>✕</button>
      </div>
    </div>
  );
}

export default function SprintDetail({ sprintId, navigate }) {
  const [sprint, setSprint] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    if (!sprintId) return;
    try {
      const [spRes, anRes] = await Promise.all([
        sprintsAPI.get(sprintId),
        analyticsAPI.getSprint(sprintId)
      ]);
      setSprint(spRes.data.sprint);
      setTasks(spRes.data.sprint.tasks || []);
      setMetrics(anRes.data.metrics);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [sprintId]);

  useEffect(() => { load(); }, [load]);

  const handleUpdate = async (taskId, data) => {
    await tasksAPI.update(taskId, data);
    load();
  };
  const handleDelete = async (taskId) => {
    if (!window.confirm("Delete this task?")) return;
    await tasksAPI.delete(taskId);
    load();
  };
  const handleComplete = async () => {
    if (!window.confirm("Mark sprint as completed? This will finalise your analytics.")) return;
    await sprintsAPI.complete(sprintId);
    navigate("sprints");
  };

  const filtered = filter === "all" ? tasks : tasks.filter(t => t.status === filter);
  const completionRate = metrics?.completion_rate ?? 0;
  const subjectScores = metrics?.subject_scores ?? {};

  if (loading) return <div className="loading"><div className="loading-spinner" /></div>;
  if (!sprint) return <div className="page-body"><div className="alert alert-info">Sprint not found.</div></div>;

  return (
    <>
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ cursor: "pointer", color: "var(--blue)", fontSize: 13 }} onClick={() => navigate("sprints")}>← Sprints</span>
            <span style={{ color: "var(--gray-300)" }}>|</span>
            <h2>{sprint.name}</h2>
            <span className={`badge badge-${sprint.status === "active" ? "in_progress" : "completed"}`}>{sprint.status}</span>
          </div>
          <p>📅 {sprint.start_date} → {sprint.end_date} ({sprint.duration_days} days)</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {sprint.status === "active" && (
            <>
              <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Task</button>
              <button className="btn btn-success" onClick={handleComplete}>✓ Complete Sprint</button>
            </>
          )}
        </div>
      </div>

      <div className="page-body">
        {/* Progress bar */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontWeight: 700, color: "var(--gray-700)" }}>Sprint Progress</span>
            <span style={{ fontWeight: 700, fontSize: 18 }}>{completionRate.toFixed(0)}%</span>
          </div>
          <div className="progress-bar-wrap" style={{ height: 12, marginBottom: 12 }}>
            <div
              className={`progress-bar-fill ${completionRate >= 70 ? "progress-green" : completionRate >= 40 ? "progress-blue" : "progress-red"}`}
              style={{ width: `${completionRate}%` }}
            />
          </div>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            {[
              ["Total Tasks", tasks.length],
              ["Completed", tasks.filter(t => t.status === "completed").length],
              ["Pending", tasks.filter(t => t.status === "pending").length],
              ["In Progress", tasks.filter(t => t.status === "in_progress").length],
              ["Consistency", metrics?.consistency_index != null ? `${(metrics.consistency_index * 100).toFixed(0)}%` : "—"],
              ["Study Hours", metrics?.total_study_hours != null ? `${metrics.total_study_hours}h` : "—"],
            ].map(([label, value]) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: "var(--navy)" }}>{value}</div>
                <div style={{ fontSize: 11, color: "var(--gray-400)" }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid-2">
          {/* Tasks panel */}
          <div>
            <div className="section-header">
              <div className="section-title">Tasks</div>
              <div className="tabs" style={{ marginBottom: 0 }}>
                {["all", "pending", "in_progress", "completed"].map(s => (
                  <div key={s} className={`tab ${filter === s ? "active" : ""}`} onClick={() => setFilter(s)} style={{ padding: "5px 12px", fontSize: 12 }}>
                    {s === "in_progress" ? "In Progress" : s.charAt(0).toUpperCase() + s.slice(1)}
                  </div>
                ))}
              </div>
            </div>
            <div className="task-list">
              {filtered.length === 0 ? (
                <div className="empty-state" style={{ padding: 40 }}>
                  <div className="empty-icon">📝</div>
                  <div className="empty-text">No {filter !== "all" ? filter : ""} tasks. {sprint.status === "active" && <span style={{ color: "var(--blue)", cursor: "pointer" }} onClick={() => setShowAdd(true)}>Add one!</span>}</div>
                </div>
              ) : (
                filtered.map(task => (
                  <TaskCard key={task.task_id} task={task} onUpdate={handleUpdate} onDelete={handleDelete} />
                ))
              )}
            </div>
          </div>

          {/* Subject analytics panel */}
          <div>
            <div className="section-title" style={{ marginBottom: 12 }}>📚 Subject Performance</div>
            {Object.keys(subjectScores).length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}>
                <div className="empty-text">Complete tasks to see subject performance.</div>
              </div>
            ) : (
              Object.entries(subjectScores)
                .sort((a, b) => a[1].score - b[1].score)
                .map(([subject, data]) => (
                  <div key={subject} className="card" style={{ marginBottom: 10, padding: "14px 16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div>
                        <span style={{ fontWeight: 600, fontSize: 14 }}>{subject}</span>
                        <span className={`badge badge-${data.classification}`} style={{ marginLeft: 8 }}>{data.classification}</span>
                      </div>
                      <span style={{ fontWeight: 700, fontSize: 16, color: data.score >= 75 ? "var(--green)" : data.score >= 50 ? "var(--blue)" : "var(--red)" }}>
                        {data.score.toFixed(0)}/100
                      </span>
                    </div>
                    <div className="progress-bar-wrap" style={{ marginBottom: 8 }}>
                      <div
                        className={`progress-bar-fill ${data.score >= 75 ? "progress-green" : data.score >= 50 ? "progress-blue" : "progress-red"}`}
                        style={{ width: `${data.score}%` }}
                      />
                    </div>
                    <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--gray-400)" }}>
                      <span>Tasks: {data.completed}/{data.total}</span>
                      <span>Time: {data.actual_hours.toFixed(1)}h / {data.target_hours.toFixed(1)}h target</span>
                    </div>
                  </div>
                ))
            )}
            {sprint.notes && (
              <div className="alert alert-info" style={{ marginTop: 16 }}>
                <strong>Sprint Goal:</strong> {sprint.notes}
              </div>
            )}
          </div>
        </div>
      </div>

      {showAdd && <AddTaskModal sprintId={sprintId} onClose={() => setShowAdd(false)} onAdded={() => { setShowAdd(false); load(); }} />}
    </>
  );
}
