import React, { useEffect, useState, useCallback } from "react";
import { sprintsAPI } from "../services/api";

function CreateSprintModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: "", start_date: "", end_date: "", notes: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Default to today → +6 days
  useEffect(() => {
    const today = new Date().toISOString().split("T")[0];
    const next = new Date(Date.now() + 6 * 86400000).toISOString().split("T")[0];
    setForm(f => ({ ...f, start_date: today, end_date: next }));
  }, []);

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const res = await sprintsAPI.create(form);
      onCreated(res.data.sprint);
    } catch (err) {
      const errs = err.response?.data?.errors || err.response?.data?.error;
      setError(typeof errs === "object" ? Object.values(errs).join(", ") : errs || "Failed to create sprint");
    } finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">🏃 Create New Sprint</div>
          <span className="modal-close" onClick={onClose}>✕</span>
        </div>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Sprint Name</label>
            <input className="form-input" placeholder="e.g. Week 3 - Exam Prep" value={form.name} onChange={set("name")} required />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input className="form-input" type="date" value={form.start_date} onChange={set("start_date")} required />
            </div>
            <div className="form-group">
              <label className="form-label">End Date</label>
              <input className="form-input" type="date" value={form.end_date} onChange={set("end_date")} required />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Goal / Notes (optional)</label>
            <textarea className="form-textarea" placeholder="What do you want to achieve this sprint?" value={form.notes} onChange={set("notes")} />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? "Creating..." : "Create Sprint"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function SprintsPage({ navigate }) {
  const [sprints, setSprints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await sprintsAPI.list({ status: statusFilter, per_page: 20 });
      setSprints(res.data.sprints);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this sprint and all its tasks?")) return;
    await sprintsAPI.delete(id);
    load();
  };

  return (
    <>
      <div className="page-header">
        <div><h2>Sprints</h2><p>Manage your study sprints</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Sprint</button>
      </div>

      <div className="page-body">
        <div className="tabs">
          {["all", "active", "completed"].map(s => (
            <div key={s} className={`tab ${statusFilter === s ? "active" : ""}`} onClick={() => setStatusFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </div>
          ))}
        </div>

        {loading ? (
          <div className="loading"><div className="loading-spinner" /></div>
        ) : sprints.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🏃</div>
            <div className="empty-title">No sprints yet</div>
            <div className="empty-text">Create your first sprint to start planning your study sessions.</div>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>Create Sprint</button>
          </div>
        ) : (
          <div className="grid-3">
            {sprints.map(sprint => {
              const start = new Date(sprint.start_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
              const end = new Date(sprint.end_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
              return (
                <div key={sprint.sprint_id} className={`sprint-card ${sprint.status}`}
                  onClick={() => navigate("sprint-detail", { sprintId: sprint.sprint_id })}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                    <div className="sprint-name">{sprint.name}</div>
                    <span className={`badge badge-${sprint.status === "active" ? "in_progress" : sprint.status === "completed" ? "completed" : "pending"}`}>
                      {sprint.status}
                    </span>
                  </div>
                  <div className="sprint-dates">📅 {start} → {end} ({sprint.duration_days} days)</div>
                  {sprint.notes && <div style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 10, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{sprint.notes}</div>}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate("sprint-detail", { sprintId: sprint.sprint_id })}>View →</button>
                    <button className="btn btn-danger btn-sm" onClick={e => handleDelete(sprint.sprint_id, e)}>Delete</button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showModal && <CreateSprintModal onClose={() => setShowModal(false)} onCreated={s => { setShowModal(false); navigate("sprint-detail", { sprintId: s.sprint_id }); }} />}
    </>
  );
}
