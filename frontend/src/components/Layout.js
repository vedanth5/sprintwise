import React from "react";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { id: "dashboard", icon: "🏠", label: "Dashboard" },
  { id: "sprints",   icon: "🏃", label: "Sprints"   },
  { id: "materials", icon: "📄", label: "Study Materials" },
  { id: "analytics", icon: "📊", label: "Analytics" },
  { id: "profile",   icon: "👤", label: "Profile"   },
];

export default function Layout({ children, page, navigate }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>⚡ SprintWise</h1>
          <span>AI Productivity</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <div
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">{user?.full_name}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>{user?.email}</div>
          <button
            className="btn btn-secondary btn-sm"
            style={{ width: "100%" }}
            onClick={logout}
          >
            Sign out →
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div key={page} className="page-view">
          {children}
        </div>
      </main>
    </div>
  );
}
