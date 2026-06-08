"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { MetricCard } from "@/components/charts/MetricCard";
import { RequestsChart } from "@/components/charts/RequestsChart";
import { CostChart } from "@/components/charts/CostChart";
import { ModelTable } from "@/components/tables/ModelTable";
import { RecentLogsTable } from "@/components/tables/RecentLogsTable";
import { LatencyChart } from "@/components/charts/LatencyChart";
import {
  Activity,
  DollarSign,
  Zap,
  AlertTriangle,
  Users,
  FolderOpen,
  Brain,
  ShieldAlert,
  Star,
  TrendingUp,
} from "lucide-react";
import {
  formatCurrency,
  formatNumber,
  formatMs,
  formatPercent,
} from "@/lib/utils";

export default function DashboardPage() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview({ days: 30 }).then((r) => r.data),
    refetchInterval: 60_000,
  });

  const metrics = [
    {
      title: "Total Requests",
      value: formatNumber(overview?.total_requests ?? 0),
      change: overview?.requests_change_pct ?? 0,
      icon: Activity,
      color: "primary" as const,
      sub: `${overview?.requests_today ?? 0} today`,
    },
    {
      title: "Total Cost",
      value: formatCurrency(overview?.total_cost ?? 0),
      change: overview?.cost_change_pct ?? 0,
      icon: DollarSign,
      color: "warning" as const,
      sub: `${formatCurrency(overview?.cost_today ?? 0)} today`,
    },
    {
      title: "Avg Latency",
      value: formatMs(overview?.avg_latency_ms ?? 0),
      icon: Zap,
      color: "accent" as const,
      sub: "P50 response time",
    },
    {
      title: "Error Rate",
      value: formatPercent(overview?.error_rate ?? 0),
      icon: AlertTriangle,
      color: (overview?.error_rate ?? 0) > 0.05 ? ("danger" as const) : ("success" as const),
      sub: "Last 30 days",
    },
    {
      title: "Active Projects",
      value: String(overview?.active_projects ?? 0),
      icon: FolderOpen,
      color: "primary" as const,
      sub: "With recent activity",
    },
    {
      title: "Active Users",
      value: String(overview?.active_users ?? 0),
      icon: Users,
      color: "accent" as const,
      sub: "Last 30 days",
    },
    {
      title: "Hallucination Rate",
      value: formatPercent(overview?.hallucination_rate ?? 0),
      icon: Brain,
      color: (overview?.hallucination_rate ?? 0) > 0.15 ? ("danger" as const) : ("success" as const),
      sub: "RAGAS faithfulness",
    },
    {
      title: "Satisfaction Score",
      value: `${((overview?.satisfaction_score ?? 0) * 20).toFixed(0)}%`,
      icon: Star,
      color: "success" as const,
      sub: `${overview?.satisfaction_score?.toFixed(1) ?? 0}/5 avg rating`,
    },
  ];

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">
            Platform Overview
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time LLM monitoring — last 30 days
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary px-3 py-1.5 rounded-lg border border-border">
          <TrendingUp className="w-3.5 h-3.5" />
          Auto-refreshes every 60s
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <MetricCard key={m.title} {...m} loading={isLoading} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RequestsChart />
        <CostChart />
      </div>

      {/* Latency Chart */}
      <LatencyChart />

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ModelTable />
        <RecentLogsTable />
      </div>
    </div>
  );
}
