"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { alertsApi, evaluationsApi, feedbackApi, analyticsApi } from "@/lib/api";
import { toast } from "sonner";
import { Bell, FlaskConical, Star, Activity, CheckCircle2, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { timeAgo, cn, formatMs, formatCurrency, formatPercent } from "@/lib/utils";

const severityColors: Record<string, string> = {
  low: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  medium: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  high: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  critical: "text-red-400 bg-red-400/10 border-red-400/20",
};

export function AlertsPageContent() {
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => alertsApi.list({ page_size: 50 }).then((r) => r.data),
  });

  const acknowledge = useMutation({
    mutationFn: (id: string) => alertsApi.acknowledge(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      toast.success("Alert acknowledged");
    },
  });

  const deleteAlert = useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const alerts = data?.items ?? [];
  const triggered = alerts.filter((a: any) => a.is_triggered && !a.is_acknowledged);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Bell className="w-5 h-5 text-amber-400" />
        <div>
          <h1 className="text-xl font-bold">Alerts</h1>
          <p className="text-sm text-muted-foreground">
            {triggered.length} active alerts
          </p>
        </div>
      </div>

      {triggered.length > 0 && (
        <div className="p-4 rounded-xl bg-red-400/10 border border-red-400/20">
          <div className="flex items-center gap-2 text-red-400 mb-2">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-semibold">{triggered.length} alerts need attention</span>
          </div>
          <div className="space-y-1.5">
            {triggered.slice(0, 3).map((a: any) => (
              <div key={a.id} className="flex items-center gap-3 text-xs">
                <Badge variant="outline" className={cn("text-[10px]", severityColors[a.severity])}>
                  {a.severity}
                </Badge>
                <span className="flex-1">{a.title}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 text-[10px]"
                  onClick={() => acknowledge.mutate(a.id)}
                >
                  Acknowledge
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card-glass rounded-xl overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-secondary/50 border-b border-border/50">
            <tr>
              {["Title", "Type", "Severity", "Status", "Threshold", "Time"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-muted-foreground font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-border/30">
                  {[...Array(6)].map((_, j) => (
                    <td key={j} className="px-4 py-3"><div className="shimmer h-4 rounded w-20" /></td>
                  ))}
                </tr>
              ))
              : alerts.map((alert: any) => (
                <tr key={alert.id} className="border-b border-border/30 hover:bg-secondary/30">
                  <td className="px-4 py-3 font-medium">{alert.title}</td>
                  <td className="px-4 py-3 capitalize text-muted-foreground">{alert.alert_type.replace(/_/g, " ")}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className={cn("text-[10px]", severityColors[alert.severity])}>
                      {alert.severity}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    {alert.is_acknowledged ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Acknowledged
                      </span>
                    ) : alert.is_triggered ? (
                      <span className="text-red-400">Triggered</span>
                    ) : (
                      <span className="text-muted-foreground">Monitoring</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono">{alert.threshold_value ?? "—"}</td>
                  <td className="px-4 py-3 text-muted-foreground">{timeAgo(alert.created_at)}</td>
                </tr>
              ))}
          </tbody>
        </table>
        {alerts.length === 0 && (
          <div className="text-center py-10 text-muted-foreground text-sm">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-40" />
            No alerts configured yet.
          </div>
        )}
      </div>
    </div>
  );
}

export function EvaluationsPageContent() {
  const { data, isLoading } = useQuery({
    queryKey: ["evaluations"],
    queryFn: () => evaluationsApi.list({ page_size: 20 }).then((r) => r.data),
  });

  const evals = data?.items ?? [];

  const scoreColor = (v: number) =>
    v >= 0.8 ? "text-emerald-400" : v >= 0.6 ? "text-amber-400" : "text-red-400";

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <FlaskConical className="w-5 h-5 text-purple-400" />
        <div>
          <h1 className="text-xl font-bold">Evaluations</h1>
          <p className="text-sm text-muted-foreground">RAGAS + DeepEval quality metrics</p>
        </div>
      </div>

      <div className="card-glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-secondary/50 border-b border-border/50">
              <tr>
                {["Project", "Faithfulness", "Relevancy", "Correctness", "Toxicity", "Quality", "Time"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(5)].map((_, i) => (
                  <tr key={i} className="border-b border-border/30">
                    {[...Array(7)].map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="shimmer h-4 rounded w-16" /></td>
                    ))}
                  </tr>
                ))
                : evals.map((e: any) => (
                  <tr key={e.id} className="border-b border-border/30 hover:bg-secondary/30">
                    <td className="px-4 py-3 font-mono text-muted-foreground">{e.project_id?.slice(0, 8)}...</td>
                    <td className={cn("px-4 py-3 font-mono font-semibold", scoreColor(e.faithfulness ?? 0))}>
                      {e.faithfulness?.toFixed(3) ?? "—"}
                    </td>
                    <td className={cn("px-4 py-3 font-mono font-semibold", scoreColor(e.answer_relevancy ?? 0))}>
                      {e.answer_relevancy?.toFixed(3) ?? "—"}
                    </td>
                    <td className={cn("px-4 py-3 font-mono font-semibold", scoreColor(e.answer_correctness ?? 0))}>
                      {e.answer_correctness?.toFixed(3) ?? "—"}
                    </td>
                    <td className={cn("px-4 py-3 font-mono", (e.toxicity_score ?? 0) > 0.3 ? "text-red-400" : "text-emerald-400")}>
                      {e.toxicity_score?.toFixed(3) ?? "—"}
                    </td>
                    <td className={cn("px-4 py-3 font-mono font-bold text-sm", scoreColor(e.overall_quality_score ?? 0))}>
                      {e.overall_quality_score?.toFixed(3) ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{timeAgo(e.created_at)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {evals.length === 0 && (
          <div className="text-center py-10 text-muted-foreground text-sm">
            <FlaskConical className="w-8 h-8 mx-auto mb-2 opacity-40" />
            No evaluations run yet.
          </div>
        )}
      </div>
    </div>
  );
}

export function FeedbackPageContent() {
  const { data: stats } = useQuery({
    queryKey: ["feedback", "stats"],
    queryFn: () => feedbackApi.stats().then((r) => r.data),
  });

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Star className="w-5 h-5 text-amber-400" />
        <div>
          <h1 className="text-xl font-bold">User Feedback</h1>
          <p className="text-sm text-muted-foreground">Response ratings and satisfaction</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Avg Rating", value: `${stats?.avg_rating?.toFixed(1) ?? "—"}/5`, icon: Star, color: "warning" },
          { label: "Total Feedback", value: String(stats?.total_feedback ?? 0), icon: Activity, color: "primary" },
          { label: "Thumbs Up", value: String(stats?.thumbs_up_count ?? 0), icon: CheckCircle2, color: "success" },
          { label: "Approval Rate", value: `${((stats?.approval_rate ?? 0) * 100).toFixed(0)}%`, icon: Star, color: "accent" },
        ].map((m) => (
          <div key={m.label} className="metric-card">
            <p className="text-xs text-muted-foreground mb-2">{m.label}</p>
            <p className="text-2xl font-bold">{m.value}</p>
          </div>
        ))}
      </div>

      <div className="card-glass rounded-xl p-8 text-center text-muted-foreground">
        <Star className="w-10 h-10 mx-auto mb-3 opacity-30 text-amber-400" />
        <p className="font-medium">Feedback Trends</p>
        <p className="text-sm mt-1">Ratings appear as users submit feedback on prompt responses.</p>
      </div>
    </div>
  );
}

export function BenchmarksPageContent() {
  const { data: models } = useQuery({
    queryKey: ["analytics", "models", "bench"],
    queryFn: () => analyticsApi.models({ days: 30 }).then((r) => r.data),
  });
  const sorted = (models ?? []).sort((a: any, b: any) => a.avg_latency_ms - b.avg_latency_ms);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Activity className="w-5 h-5 text-cyan-400" />
        <div>
          <h1 className="text-xl font-bold">Model Benchmarks</h1>
          <p className="text-sm text-muted-foreground">Compare LLM providers and models</p>
        </div>
      </div>

      <div className="card-glass rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-border/50 flex items-center gap-2">
          <p className="text-sm font-semibold">Benchmark Leaderboard</p>
          <Badge variant="outline" className="text-[10px] ml-auto">Sorted by Latency</Badge>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-secondary/50">
              <tr>
                {["Rank", "Model", "Provider", "Requests", "Avg Latency", "Avg Cost", "Error Rate", "Score"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((m: any, i: number) => {
                const score = Math.max(0, 100 - (m.avg_latency_ms / 50) - (m.error_rate * 200) - (m.avg_cost * 1000));
                return (
                  <tr key={m.model_name} className="border-b border-border/30 hover:bg-secondary/30">
                    <td className="px-4 py-3">
                      <span className={cn("font-bold text-sm", i === 0 ? "text-amber-400" : i === 1 ? "text-slate-400" : i === 2 ? "text-amber-700" : "text-muted-foreground")}>
                        #{i + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium">{m.model_name}</td>
                    <td className="px-4 py-3 capitalize text-muted-foreground">{m.provider}</td>
                    <td className="px-4 py-3 font-mono">{m.total_requests}</td>
                    <td className="px-4 py-3 font-mono text-cyan-400">{formatMs(m.avg_latency_ms)}</td>
                    <td className="px-4 py-3 font-mono text-amber-400">{formatCurrency(m.avg_cost, 6)}</td>
                    <td className="px-4 py-3 font-mono">{formatPercent(m.error_rate)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden w-16">
                          <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(100, score)}%` }} />
                        </div>
                        <span className="font-semibold text-primary">{Math.round(score)}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
