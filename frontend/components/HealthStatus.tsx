"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { HealthResponse } from "@/types/api";

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to connect to Priya backend"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur">
      <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80">
        <div>
          <h2 className="text-base font-semibold text-white">
            Backend & System Health
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time status of Priya API service and PostgreSQL storage
          </p>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition disabled:opacity-50"
        >
          {loading ? "Checking..." : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {/* API Status */}
        <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/50">
          <span className="text-xs font-medium text-zinc-400">API Status</span>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                health?.status === "healthy"
                  ? "bg-emerald-400 animate-pulse"
                  : health?.status === "degraded"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-rose-500"
              }`}
            />
            <span className="text-sm font-semibold capitalize text-zinc-100">
              {health?.status || (error ? "Offline" : "Checking...")}
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-1">
            {health?.environment
              ? `Env: ${health.environment}`
              : error
              ? "Backend unreachable"
              : "Connecting..."}
          </p>
        </div>

        {/* Database Status */}
        <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/50">
          <span className="text-xs font-medium text-zinc-400">
            PostgreSQL Database
          </span>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                health?.database?.connected ? "bg-emerald-400" : "bg-rose-500"
              }`}
            />
            <span className="text-sm font-semibold capitalize text-zinc-100">
              {health?.database?.connected ? "Connected" : "Disconnected"}
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-1">
            {health?.database?.latency_ms !== null &&
            health?.database?.latency_ms !== undefined
              ? `Latency: ${health.database.latency_ms} ms`
              : "No connection established"}
          </p>
        </div>

        {/* Timezone & Clock */}
        <div className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/50">
          <span className="text-xs font-medium text-zinc-400">
            Presentation Timezone
          </span>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-sm font-semibold text-zinc-100">
              {health?.timezone || "Africa/Lagos"}
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-1 truncate">
            {health?.timestamp_utc
              ? `Sync: ${new Date(health.timestamp_utc).toLocaleTimeString()}`
              : "Awaiting sync"}
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
          <strong className="font-semibold">Connection Notice:</strong> {error}.
          Make sure the backend is running (`uvicorn app.main:app`).
        </div>
      )}
    </div>
  );
};
