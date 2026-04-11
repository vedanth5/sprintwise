import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { authAPI } from "../services/api";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    academic_level: user?.academic_level || "undergraduate",
    weekly_study_target_hours: user?.weekly_study_target_hours || 20,
    subjects: (user?.subjects || []).join(", "),
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setSaved(false);
    try {
      const subjects = form.subjects.split(",").map(s => s.trim()).filter(Boolean);
      const res = await authAPI.updateProfile({ ...form, subjects, weekly_study_target_hours: parseFloat(form.weekly_study_target_hours) });
      updateUser(res.data.user);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to update profile");
    }
  };

  return (
    <>
      <div className="page-header">
        <div><h2>Profile</h2><p>Manage your account and study preferences</p></div>
      </div>
      <div className="page-body" style={{ maxWidth: 600 }}>
        {saved && <div className="alert alert-success">✅ Profile updated successfully!</div>}
        {error && <div className="auth-error">{error}</div>}

        <div className="card">
          <form onSubmit={submit}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" value={form.full_name} onChange={set("full_name")} required />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" value={user?.email || ""} disabled style={{ opacity: 0.6 }} />
              <div className="form-error" style={{ color: "var(--gray-400)" }}>Email cannot be changed</div>
            </div>
            <div className="form-group">
              <label className="form-label">Academic Level</label>
              <select className="form-select" value={form.academic_level} onChange={set("academic_level")}>
                <option value="undergraduate">Undergraduate</option>
                <option value="postgraduate">Postgraduate</option>
                <option value="competitive">Competitive Exam Aspirant</option>
                <option value="self_learner">Self Learner</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Weekly Study Target (hours)</label>
              <input className="form-input" type="number" min="1" max="100" value={form.weekly_study_target_hours} onChange={set("weekly_study_target_hours")} />
              <div style={{ fontSize: 12, color: "var(--gray-400)", marginTop: 4 }}>Used by the AI engine to compute subject time targets</div>
            </div>
            <div className="form-group">
              <label className="form-label">Subjects (comma-separated)</label>
              <input className="form-input" placeholder="Mathematics, Physics, Chemistry" value={form.subjects} onChange={set("subjects")} />
              <div style={{ fontSize: 12, color: "var(--gray-400)", marginTop: 4 }}>Used to detect missing subjects in sprints</div>
            </div>
            <button type="submit" className="btn btn-primary">Save Changes</button>
          </form>
        </div>

        <div className="card" style={{ marginTop: 20 }}>
          <div className="section-title" style={{ marginBottom: 12 }}>Account Info</div>
          {[
            ["Member since", new Date(user?.created_at).toLocaleDateString()],
            ["Account type", user?.academic_level],
            ["Study target", `${user?.weekly_study_target_hours}h / week`],
          ].map(([label, value]) => (
            <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--gray-100)", fontSize: 14 }}>
              <span style={{ color: "var(--gray-500)" }}>{label}</span>
              <span style={{ fontWeight: 500 }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
