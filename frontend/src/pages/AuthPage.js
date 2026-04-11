import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [tab, setTab] = useState("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    email: "", password: "", full_name: "",
    academic_level: "undergraduate", weekly_study_target_hours: 20
  });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      if (tab === "login") {
        await login(form.email, form.password);
      } else {
        await register(form);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.errors
        ? Object.values(err.response.data.errors || {}).join(", ")
        : "An error occurred. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>⚡ SprintWise</h1>
          <p>AI-Powered Student Productivity Platform</p>
        </div>

        <div className="auth-tabs">
          <div className={`auth-tab ${tab === "login" ? "active" : ""}`} onClick={() => { setTab("login"); setError(""); }}>Sign In</div>
          <div className={`auth-tab ${tab === "register" ? "active" : ""}`} onClick={() => { setTab("register"); setError(""); }}>Register</div>
        </div>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {tab === "register" && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" type="text" placeholder="Jane Doe" value={form.full_name} onChange={set("full_name")} required />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" placeholder="student@example.com" value={form.email} onChange={set("email")} required />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" placeholder="Min 8 characters" value={form.password} onChange={set("password")} required />
          </div>

          {tab === "register" && (
            <>
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
              </div>
            </>
          )}

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
            {loading ? "Please wait..." : tab === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: 12, color: "var(--gray-400)", marginTop: 20 }}>
          Plan smarter. Study consistently. Improve daily.
        </p>
      </div>
    </div>
  );
}
