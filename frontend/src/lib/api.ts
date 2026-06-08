import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) throw new Error("No refresh token");
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refresh,
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => api.post("/auth/register", data),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),
  changePassword: (current: string, next: string) =>
    api.post("/auth/change-password", {
      current_password: current,
      new_password: next,
    }),
  requestReset: (email: string) =>
    api.post("/auth/password-reset/request", { email }),
  confirmReset: (token: string, password: string) =>
    api.post("/auth/password-reset/confirm", {
      token,
      new_password: password,
    }),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: (params?: { project_id?: string; days?: number }) =>
    api.get("/analytics/overview", { params }),
  timeseries: (params: {
    metric: string;
    granularity?: string;
    days?: number;
    project_id?: string;
  }) => api.get("/analytics/timeseries", { params }),
  models: (params?: { days?: number; project_id?: string }) =>
    api.get("/analytics/models", { params }),
  latencyPercentiles: (params?: { project_id?: string; days?: number }) =>
    api.get("/analytics/latency/percentiles", { params }),
  costForecast: (params?: { project_id?: string }) =>
    api.get("/analytics/costs/forecast", { params }),
};

// ── Projects ──────────────────────────────────────────────────────────────────
export const projectsApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get("/projects/", { params }),
  create: (data: { name: string; description?: string; environment?: string }) =>
    api.post("/projects/", data),
  get: (id: string) => api.get(`/projects/${id}`),
  update: (id: string, data: object) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  createApiKey: (projectId: string, data: object) =>
    api.post(`/projects/${projectId}/api-keys`, data),
  listApiKeys: (projectId: string) =>
    api.get(`/projects/${projectId}/api-keys`),
  revokeApiKey: (projectId: string, keyId: string) =>
    api.delete(`/projects/${projectId}/api-keys/${keyId}`),
};

// ── Logs ──────────────────────────────────────────────────────────────────────
export const logsApi = {
  list: (params?: object) => api.get("/logs/", { params }),
  get: (id: string) => api.get(`/logs/${id}`),
  track: (data: object) => api.post("/logs/track", data),
  delete: (id: string) => api.delete(`/logs/${id}`),
};

// ── Evaluations ──────────────────────────────────────────────────────────────
export const evaluationsApi = {
  list: (params?: object) => api.get("/evaluations/", { params }),
  run: (data: object) => api.post("/evaluations/", data),
};

// ── Alerts ────────────────────────────────────────────────────────────────────
export const alertsApi = {
  list: (params?: object) => api.get("/alerts/", { params }),
  create: (data: object) => api.post("/alerts/", data),
  acknowledge: (id: string) => api.put(`/alerts/${id}/acknowledge`),
  delete: (id: string) => api.delete(`/alerts/${id}`),
};

// ── Feedback ──────────────────────────────────────────────────────────────────
export const feedbackApi = {
  submit: (data: object) => api.post("/feedback/", data),
  stats: (params?: object) => api.get("/feedback/stats", { params }),
};

// ── Security ──────────────────────────────────────────────────────────────────
export const securityApi = {
  events: (params?: object) => api.get("/security/events", { params }),
  stats: (params?: object) => api.get("/security/stats", { params }),
};

// ── Copilot ────────────────────────────────────────────────────────────────────
export const copilotApi = {
  chat: (data: { question: string; project_id?: string }) =>
    api.post("/copilot/chat", data),
  suggestions: () => api.get("/copilot/suggestions"),
};

// ── Users (Admin) ──────────────────────────────────────────────────────────────
export const usersApi = {
  list: (params?: object) => api.get("/users/", { params }),
  updateRole: (id: string, role: string) =>
    api.put(`/users/${id}/role`, { role }),
  toggleStatus: (id: string) => api.put(`/users/${id}/status`),
};
