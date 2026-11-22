import { HealthResponse } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options?.headers || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMessage = `API request failed with status ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData?.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Keep generic message if response body is not JSON
        }
        throw new Error(errorMessage);
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error("Network request failed");
    }
  }

  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }
}

export const api = new ApiClient(API_BASE_URL);
