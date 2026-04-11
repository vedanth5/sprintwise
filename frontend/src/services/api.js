/**
 * SprintWise - Axios API Service
 * Centralised HTTP client with JWT auth and token refresh interceptors.
 */
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

/* ── Request interceptor: attach access token ── */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/* ── Response interceptor: handle 401 / token refresh ── */
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");
        const res = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });
        const newToken = res.data.access_token;
        localStorage.setItem("access_token", newToken);
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/* ── Auth ── */
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  verifyOtp: (data) => api.post("/auth/verify-otp", data),
  resendOtp: (data) => api.post("/auth/resend-otp", data),
  me: () => api.get("/auth/me"),
  updateProfile: (data) => api.put("/auth/profile", data),
};

/* ── Sprints ── */
export const sprintsAPI = {
  list: (params) => api.get("/sprints/", { params }),
  create: (data) => api.post("/sprints/", data),
  get: (id) => api.get(`/sprints/${id}`),
  update: (id, data) => api.put(`/sprints/${id}`, data),
  complete: (id) => api.patch(`/sprints/${id}/complete`),
  delete: (id) => api.delete(`/sprints/${id}`),
};

/* ── Tasks ── */
export const tasksAPI = {
  create: (data) => api.post("/tasks/", data),
  createBulk: (data) => api.post("/tasks/bulk", data),
  getForSprint: (sprintId, params) => api.get(`/tasks/sprint/${sprintId}`, { params }),
  update: (id, data) => api.patch(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
};

/* ── Time Logs ── */
export const timelogsAPI = {
  start: (taskId) => api.post("/timelogs/start", { task_id: taskId }),
  stop: (logId, taskId) => api.post("/timelogs/stop", { log_id: logId, task_id: taskId }),
  getForTask: (taskId) => api.get(`/timelogs/task/${taskId}`),
  getActive: () => api.get("/timelogs/active"),
};

/* ── Analytics ── */
export const analyticsAPI = {
  getSprint: (sprintId) => api.get(`/analytics/sprint/${sprintId}`),
  getHistory: () => api.get("/analytics/history"),
  getAnomaly: () => api.get("/analytics/anomaly"),
};

/* ── Recommendations ── */
export const recommendationsAPI = {
  get: () => api.get("/recommendations/"),
  dismiss: (id) => api.patch(`/recommendations/${id}/dismiss`),
  getAll: () => api.get("/recommendations/all"),
};

/* ── Dashboard ── */
export const dashboardAPI = {
  getSummary: () => api.get("/dashboard/summary"),
};

/* ── Materials (PDF processing) ── */
export const materialsAPI = {
  upload: (formData) => api.post("/materials/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  }),
  list: () => api.get("/materials/"),
  get: (id) => api.get(`/materials/${id}`),
};

export default api;
