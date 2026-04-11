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
          <span>AI Productivity Platform</span>
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
          <div>{user?.email}</div>
          <div
            style={{ marginTop: 10, cursor: "pointer", color: "rgba(255,255,255,0.5)", fontSize: 12 }}
            onClick={logout}
          >
            Sign out →
          </div>
        </div>
      </aside>

      <main className="main-content">{children}</main>
    </div>
  );
}
