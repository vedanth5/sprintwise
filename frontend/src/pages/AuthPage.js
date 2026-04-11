import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const { login, register, verifyOtp, resendOtp } = useAuth();
  const [tab, setTab] = useState("login");
  const [step, setStep] = useState("form"); // form, verify
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [otpCode, setOtpCode] = useState("");
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
        setStep("verify");
      }
    } catch (err) {
      if (err.response?.data?.needs_verification) {
        setForm(f => ({ ...f, email: err.response.data.email }));
        setStep("verify");
        setError("Account not verified. Please enter the code sent to your email.");
      } else {
        setError(err.response?.data?.error || "An error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    if (otpCode.length !== 6) return setError("Enter a 6-digit code.");
    setError(""); setLoading(true);
    try {
      await verifyOtp(form.email, otpCode);
    } catch (err) {
      setError(err.response?.data?.error || "Invalid or expired code.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    try {
      await resendOtp(form.email);
      setError("New code sent to your email.");
    } catch (err) {
      setError("Failed to resend code.");
    }
  };

  if (step === "verify") {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <h1 className="text-gradient">Verify Email</h1>
            <p>We've sent a 6-digit code to <strong>{form.email}</strong></p>
          </div>

          {error && <div className={`auth-error ${error.includes("sent") ? "success" : ""}`} style={{ 
            background: error.includes("sent") ? "var(--green-bg)" : "var(--red-bg)",
            color: error.includes("sent") ? "var(--green)" : "var(--red)",
            borderColor: error.includes("sent") ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"
          }}>{error}</div>}

          <form onSubmit={handleVerify}>
            <div className="form-group" style={{ textAlign: "center" }}>
              <label className="form-label" style={{ marginBottom: 12 }}>Enter OTP Code</label>
              <input 
                className="form-input" 
                type="text" 
                maxLength="6" 
                placeholder="000000" 
                value={otpCode}
                onChange={e => setOtpCode(e.target.value.replace(/\D/g, ""))}
                style={{ 
                  fontSize: 32, 
                  textAlign: "center", 
                  letterSpacing: "0.5em", 
                  fontWeight: "800",
                  padding: "16px"
                }} 
                required 
                autoFocus 
              />
            </div>

            <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", marginTop: 12 }}>
              {loading ? "Verifying..." : "Verify & Continue →"}
            </button>
          </form>

          <div style={{ textAlign: "center", marginTop: 24 }}>
            <p style={{ fontSize: 13 }}>Didn't receive the code?</p>
            <button className="btn btn-secondary" onClick={handleResend} style={{ marginTop: 8, fontSize: 12 }}>
              Resend Code
            </button>
            <div style={{ marginTop: 16 }}>
              <button 
                className="btn btn-sm" 
                style={{ fontSize: 12, color: "var(--accent)", background: "transparent" }}
                onClick={() => { setStep("form"); setTab("login"); setError(""); }}
              >
                ← Back to Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1 className="text-gradient">⚡ SprintWise</h1>
          <p>{tab === "login" ? "Welcome back! Ready for a sprint?" : "Start your productivity journey today."}</p>
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
            <label className="form-label">Email Address</label>
            <input className="form-input" type="email" placeholder="student@example.com" value={form.email} onChange={set("email")} required autoFocus />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" placeholder="••••••••" value={form.password} onChange={set("password")} required />
          </div>

          {tab === "register" && (
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Level</label>
                <select className="form-select" value={form.academic_level} onChange={set("academic_level")}>
                  <option value="undergraduate">Undergrad</option>
                  <option value="postgraduate">Postgrad</option>
                  <option value="competitive">Competitive</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Hours/Wk</label>
                <input className="form-input" type="number" min="1" max="100" value={form.weekly_study_target_hours} onChange={set("weekly_study_target_hours")} />
              </div>
            </div>
          )}

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", marginTop: 12 }}>
            {loading ? "Processing..." : tab === "login" ? "Sign In →" : "Create Account →"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: 13, color: "var(--text-muted)", marginTop: 24 }}>
          Plan smarter. Study consistently. Improve daily.
        </p>
      </div>
    </div>
  );
}
