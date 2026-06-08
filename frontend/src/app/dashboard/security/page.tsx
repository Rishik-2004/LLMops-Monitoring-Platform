"use client";

import { useQuery } from "@tanstack/react-query";
import { securityApi } from "@/lib/api";
import { ShieldAlert, AlertTriangle, Shield, Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { timeAgo, cn } from "@/lib/utils";
import { MetricCard } from "@/components/charts/MetricCard";

const threatColors: Record<string, string> = {
  prompt_injection: "text-red-400 bg-red-400/10 border-red-400/20",
  jailbreak: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  toxicity: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  system_prompt_extraction: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  suspicious: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
  clean: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
};

export default function SecurityPage() {
  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ["security", "events"],
    queryFn: () => securityApi.events({ page_size: 50 }).then((r) => r.data),
  });

  const { data: stats } = useQuery({
    queryKey: ["security", "stats"],
    queryFn: () => securityApi.stats().then((r) => r.data),
  });

  const riskLevel = stats?.risk_level ?? "low";
  const riskColor =
    riskLevel === "high" ? "danger" : riskLevel === "medium" ? "warning" : "success";

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <ShieldAlert className="w-5 h-5 text-red-400" />
        <div>
          <h1 className="text-xl font-bold">Security Monitor</h1>
          <p className="text-sm text-muted-foreground">
            Prompt injection, jailbreak, and toxicity detection
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Threats (30d)"
          value={String(stats?.total_threats_30d ?? 0)}
          icon={ShieldAlert}
          color={riskColor as any}
          loading={!stats}
        />
        <MetricCard
          title="Risk Level"
          value={riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
          icon={AlertTriangle}
          color={riskColor as any}
          loading={!stats}
        />
        <MetricCard
          title="Injection Attempts"
          value={String(
            stats?.breakdown?.find((b: any) => b.threat_type === "prompt_injection")?.count ?? 0
          )}
          icon={Activity}
          color="danger"
          loading={!stats}
        />
        <MetricCard
          title="Toxicity Detections"
          value={String(
            stats?.breakdown?.find((b: any) => b.threat_type === "toxicity")?.count ?? 0
          )}
          icon={Shield}
          color="warning"
          loading={!stats}
        />
      </div>

      {/* Threat Breakdown */}
      {stats?.breakdown?.length > 0 && (
        <div className="card-glass rounded-xl p-5">
          <p className="text-sm font-semibold mb-4">Threat Breakdown</p>
          <div className="space-y-2.5">
            {stats.breakdown.map((b: any) => (
              <div key={b.threat_type} className="flex items-center gap-3">
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px] px-2 py-0.5 w-40 justify-center",
                    threatColors[b.threat_type] ?? threatColors.suspicious
                  )}
                >
                  {b.threat_type.replace(/_/g, " ")}
                </Badge>
                <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-400/60 rounded-full"
                    style={{
                      width: `${Math.min(100, (b.count / (stats.total_threats_30d || 1)) * 100)}%`,
                    }}
                  />
                </div>
                <span className="text-xs font-mono w-8 text-right">{b.count}</span>
                <span className="text-xs text-muted-foreground w-16">
                  avg {b.avg_score.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events Table */}
      <div className="card-glass rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-border/50">
          <p className="text-sm font-semibold">Security Events</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-secondary/50">
              <tr>
                {["Threat Type", "Score", "Detection Reason", "Blocked", "Time"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-muted-foreground font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {eventsLoading
                ? [...Array(5)].map((_, i) => (
                    <tr key={i} className="border-b border-border/30">
                      {[...Array(5)].map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="shimmer h-4 rounded w-24" />
                        </td>
                      ))}
                    </tr>
                  ))
                : (events?.items ?? []).map((ev: any) => (
                    <tr key={ev.id} className="border-b border-border/30 hover:bg-secondary/30">
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-[10px]",
                            threatColors[ev.threat_type] ?? threatColors.suspicious
                          )}
                        >
                          {ev.threat_type.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-red-400">
                        {ev.threat_score.toFixed(3)}
                      </td>
                      <td className="px-4 py-3 max-w-[300px] truncate text-muted-foreground">
                        {ev.detection_reason ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {ev.is_blocked ? (
                          <Badge variant="outline" className="text-[10px] text-red-400 bg-red-400/10 border-red-400/20">
                            Blocked
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] text-amber-400 bg-amber-400/10 border-amber-400/20">
                            Flagged
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                        {timeAgo(ev.created_at)}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
        {events?.items?.length === 0 && (
          <div className="text-center py-10 text-muted-foreground text-sm">
            <Shield className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
            No security events detected. Your platform looks clean!
          </div>
        )}
      </div>
    </div>
  );
}
