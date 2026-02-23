import { getToken } from "./auth";
import type {
  Token,
  User,
  RegisterData,
  Client,
  TrustScore,
  TrainingRound,
  RoundDetail,
  ClientUpdate,
  OverviewMetrics,
  AUCHistoryItem,
  LossHistoryItem,
  AggregationStats,
  InferenceResult,
} from "./types";

const API_BASE = "/api";

function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

function getAuthHeaders(): HeadersInit {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.name = "ApiError";
  }
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let detail = "An unexpected error occurred";
    try {
      const errorData = await response.json();
      detail = typeof errorData.detail === "string"
        ? errorData.detail
        : Array.isArray(errorData.detail)
          ? errorData.detail.map((e: any) => e.msg).join(", ")
          : JSON.stringify(errorData);
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// ---------- Auth ----------

export async function login(
  email: string,
  password: string
): Promise<Token> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    let detail = "Login failed";
    try {
      const errorData = await response.json();
      detail = typeof errorData.detail === "string"
        ? errorData.detail
        : "Invalid email or password";
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export async function register(data: RegisterData): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---------- Clients ----------

export async function getClients(): Promise<Client[]> {
  return apiFetch<Client[]>("/clients");
}

export async function getClient(id: number): Promise<Client> {
  return apiFetch<Client>(`/clients/${id}`);
}

export async function getClientTrust(
  id: number
): Promise<TrustScore[]> {
  return apiFetch<TrustScore[]>(`/clients/${id}/trust`);
}

export async function updateClientStatus(
  id: number,
  status: string
): Promise<Client> {
  return apiFetch<Client>(`/clients/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ---------- Training Rounds ----------

export async function getTrainingRounds(
  skip: number = 0,
  limit: number = 50
): Promise<TrainingRound[]> {
  return apiFetch<TrainingRound[]>(
    `/training/rounds?skip=${skip}&limit=${limit}`
  );
}

export async function getCurrentRound(): Promise<TrainingRound | null> {
  try {
    return await apiFetch<TrainingRound>("/training/rounds/current");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function getRoundDetail(
  id: number
): Promise<RoundDetail> {
  return apiFetch<RoundDetail>(`/training/rounds/${id}`);
}

export async function getRoundUpdates(
  id: number
): Promise<ClientUpdate[]> {
  return apiFetch<ClientUpdate[]>(`/training/rounds/${id}/updates`);
}

// ---------- Metrics ----------

export async function getOverview(): Promise<OverviewMetrics> {
  return apiFetch<OverviewMetrics>("/metrics/overview");
}

export async function getAUCHistory(): Promise<AUCHistoryItem[]> {
  return apiFetch<AUCHistoryItem[]>("/metrics/auc-history");
}

export async function getLossHistory(): Promise<LossHistoryItem[]> {
  return apiFetch<LossHistoryItem[]>("/metrics/loss-history");
}

export async function getAggregationStats(): Promise<
  AggregationStats[]
> {
  return apiFetch<AggregationStats[]>("/metrics/aggregation-stats");
}

// ---------- Inference ----------

export async function uploadXray(file: File): Promise<InferenceResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/inference/predict`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    let detail = "Upload failed";
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

export async function getInferenceHistory(): Promise<
  InferenceResult[]
> {
  return apiFetch<InferenceResult[]>("/inference/history");
}
