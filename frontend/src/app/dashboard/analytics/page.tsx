"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { BarChart3, TrendingUp, DollarSign, Zap, Activity } from "lucide-react";
import { MetricCard } from "@/components/charts/MetricCard";
import { RequestsChart } from "@/components/charts/RequestsChart";
import { CostChart } from "@/components/charts/CostChart";
import { LatencyChart } from "@/components/charts/LatencyChart";
import { formatNumber, formatCurrency, formatMs, formatPercent } from "@/lib/utils";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, Legend
} from "recharts";

export default function AnalyticsPage() {
  const { data: overview } = useQuery({
    queryKey: ["analytics", "overview", "90d"],
    queryFn: () => analyticsApi.overview({ days: 90 }).then((r) => r.data),
  });

  const { data: models } = useQuery({
    queryKey: ["analytics", "models", "90d"],
    queryFn: () => analyticsApi.models({ days: 90 }).then((r) => r.data),
  });

  const { data: forecast } = useQuery({
    queryKey: ["analytics", "forecast"],
    queryFn: () => analyticsApi.costForecast().then((r) => r.data),
  });

  const radarData = (models ?? []).slice(0, 5).map((m: any) => ({
    model: m.model_name.replace("llama-", "").replace("-versatile", ""),
    requests: m.total_requests,
    latency: Math.round(m.avg_latency_ms / 100),
    cost: Math.round(m.avg_cost * 10000),
    errors: Math.round(m.error_rate * 100),
  }));

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <BarChart3 className="w-5 h-5 text-primary" />
        <div>
          <h1 className="text-xl font-bold">Analytics</h1>
          <p className="text-sm text-muted-foreground">90-day deep analysis</p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="Total Requests" value={formatNumber(overview?.total_requests ?? 0)} icon={Activity} color="primary" />
        <MetricCard title="Total Cost" value={formatCurrency(overview?.total_cost ?? 0)} icon={DollarSign} color="warning" />
        <MetricCard title="Avg Latency" value={formatMs(overview?.avg_latency_ms ?? 0)} icon={Zap} color="accent" />
        <MetricCard title="Error Rate" value={formatPercent(overview?.error_rate ?? 0)} icon={TrendingUp} color="danger" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RequestsChart />
        <CostChart />
      </div>

      <LatencyChart />

      {/* Cost Forecast */}
      {forecast && (
        <div className="card-glass rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <p className="text-sm font-semibold">Cost Forecast</p>
            <span className="text-xs text-muted-foreground ml-auto">
              Projected monthly: {formatCurrency(forecast.projected_monthly)}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {forecast.forecast?.slice(0, 4).map((f: any) => (
              <div key={f.date} className="p-3 bg-secondary/50 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground">{new Date(f.date).toLocaleDateString("en", { month: "short", day: "numeric" })}</p>
                <p className="font-semibold text-amber-400 text-sm mt-1">{formatCurrency(f.projected_cost)}</p>
                <p className="text-[10px] text-muted-foreground">projected</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Model Radar */}
      {radarData.length > 0 && (
        <div className="card-glass rounded-xl p-5">
          <p className="text-sm font-semibold mb-4">Model Comparison Radar</p>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="hsl(222 47% 14%)" />
              <PolarAngleAxis dataKey="model" tick={{ fontSize: 11, fill: "hsl(215 20% 55%)" }} />
              <PolarRadiusAxis tick={{ fontSize: 10, fill: "hsl(215 20% 55%)" }} />
              <Radar name="Requests" dataKey="requests" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} />
              <Radar name="Latency" dataKey="latency" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.15} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
