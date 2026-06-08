"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, logsApi } from "@/lib/api";
import { formatMs, formatCurrency, formatPercent, timeAgo } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { Activity, FileText, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function ModelTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "models"],
    queryFn: () => analyticsApi.models({ days: 7 }).then((r) => r.data),
  });

  return (
    <div className="card-glass rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4 text-indigo-400" />
        <p className="text-sm font-semibold">Model Performance</p>
        <Badge variant="outline" className="text-[10px] ml-auto">
          Last 7 days
        </Badge>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="shimmer h-10 rounded" />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-muted-foreground border-b border-border/50">
                <th className="text-left py-2 font-medium">Model</th>
                <th className="text-right py-2 font-medium">Requests</th>
                <th className="text-right py-2 font-medium">Latency</th>
                <th className="text-right py-2 font-medium">Cost</th>
                <th className="text-right py-2 font-medium">Errors</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).slice(0, 6).map((row: any, i: number) => (
                <tr
                  key={i}
                  className="border-b border-border/30 hover:bg-secondary/30 transition-colors"
                >
                  <td className="py-2.5">
                    <div>
                      <p className="font-medium truncate max-w-[120px]">
                        {row.model_name}
                      </p>
                      <p className="text-muted-foreground capitalize">
                        {row.provider}
                      </p>
                    </div>
                  </td>
                  <td className="text-right py-2.5 font-mono">
                    {row.total_requests?.toLocaleString()}
                  </td>
                  <td className="text-right py-2.5 text-cyan-400 font-mono">
                    {formatMs(row.avg_latency_ms)}
                  </td>
                  <td className="text-right py-2.5 text-amber-400 font-mono">
                    {formatCurrency(row.avg_cost, 6)}
                  </td>
                  <td className="text-right py-2.5">
                    <span
                      className={cn(
                        "font-mono",
                        row.error_rate > 0.05
                          ? "text-red-400"
                          : "text-emerald-400"
                      )}
                    >
                      {formatPercent(row.error_rate)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const statusColors: Record<string, string> = {
  success: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  error: "text-red-400 bg-red-400/10 border-red-400/20",
  timeout: "text-amber-400 bg-amber-400/10 border-amber-400/20",
};

export function RecentLogsTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["logs", "recent"],
    queryFn: () =>
      logsApi.list({ page: 1, page_size: 6 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const logs = data?.items ?? [];

  return (
    <div className="card-glass rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-4 h-4 text-cyan-400" />
        <p className="text-sm font-semibold">Recent Requests</p>
        <Badge variant="outline" className="text-[10px] ml-auto">
          Live
        </Badge>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="shimmer h-12 rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-1.5">
          {logs.map((log: any) => (
            <div
              key={log.id}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
            >
              {log.is_flagged && (
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate text-foreground/90">
                  {log.user_prompt?.slice(0, 50)}...
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {log.model_name} · {log.provider}
                </p>
              </div>
              <div className="text-right shrink-0">
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px] px-1.5 py-0",
                    statusColors[log.status] ?? statusColors.success
                  )}
                >
                  {log.status}
                </Badge>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {timeAgo(log.created_at)}
                </p>
              </div>
            </div>
          ))}
          {logs.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-6">
              No logs yet. Start tracking requests with the SDK.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
