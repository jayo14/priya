export interface DatabaseHealth {
  connected: boolean;
  status: string;
  latency_ms: number | null;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "error";
  app_name: string;
  environment: string;
  timestamp_utc: string;
  timezone: string;
  database: DatabaseHealth;
}

export interface ApiError {
  message: string;
  status?: number;
}
