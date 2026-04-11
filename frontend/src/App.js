import React from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import AuthPage from "./pages/AuthPage";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import SprintsPage from "./pages/SprintsPage";
import SprintDetail from "./pages/SprintDetail";
import AnalyticsPage from "./pages/AnalyticsPage";
import ProfilePage from "./pages/ProfilePage";
import MaterialsPage from "./pages/MaterialsPage";
import "./index.css";

function AppRoutes() {
  const { user, loading } = useAuth();
  const [page, setPage] = React.useState("dashboard");
  const [selectedSprintId, setSelectedSprintId] = React.useState(null);

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div><div className="loading-spinner" /><p>Loading SprintWise...</p></div>
      </div>
    );
  }

  if (!user) return <AuthPage />;

  const navigate = (p, extra = {}) => {
    setPage(p);
    if (extra.sprintId) setSelectedSprintId(extra.sprintId);
  };

  const renderPage = () => {
    switch (page) {
      case "dashboard": return <Dashboard navigate={navigate} />;
      case "sprints": return <SprintsPage navigate={navigate} />;
      case "sprint-detail": return <SprintDetail sprintId={selectedSprintId} navigate={navigate} />;
      case "analytics": return <AnalyticsPage />;
      case "materials": return <MaterialsPage />;
      case "profile": return <ProfilePage />;
      default: return <Dashboard navigate={navigate} />;
    }
  };

  return <Layout page={page} navigate={navigate}>{renderPage()}</Layout>;
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>;
}
