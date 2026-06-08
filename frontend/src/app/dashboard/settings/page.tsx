"use client";

import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/lib/api";
import { toast } from "sonner";
import { Settings, User, Key, Bell, Shield, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [pwdForm, setPwdForm] = useState({ current: "", next: "", confirm: "" });
  const [loading, setLoading] = useState(false);

  const changePassword = async () => {
    if (pwdForm.next !== pwdForm.confirm) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword(pwdForm.current, pwdForm.next);
      toast.success("Password changed successfully");
      setPwdForm({ current: "", next: "", confirm: "" });
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-2xl">
      <div className="flex items-center gap-3">
        <Settings className="w-5 h-5 text-primary" />
        <h1 className="text-xl font-bold">Settings</h1>
      </div>

      {/* Profile */}
      <div className="card-glass rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-4 h-4 text-primary" />
          <p className="text-sm font-semibold">Profile</p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-xs">Username</Label>
            <Input value={user?.username ?? ""} disabled className="mt-1 bg-secondary/50 border-border text-sm" />
          </div>
          <div>
            <Label className="text-xs">Email</Label>
            <Input value={user?.email ?? ""} disabled className="mt-1 bg-secondary/50 border-border text-sm" />
          </div>
          <div>
            <Label className="text-xs">Full Name</Label>
            <Input value={user?.full_name ?? ""} disabled className="mt-1 bg-secondary/50 border-border text-sm" />
          </div>
          <div>
            <Label className="text-xs">Role</Label>
            <Input value={user?.role ?? ""} disabled className="mt-1 bg-secondary/50 border-border text-sm capitalize" />
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card-glass rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Key className="w-4 h-4 text-amber-400" />
          <p className="text-sm font-semibold">Change Password</p>
        </div>
        <div className="space-y-3">
          <div>
            <Label className="text-xs">Current Password</Label>
            <Input
              type="password"
              value={pwdForm.current}
              onChange={(e) => setPwdForm((p) => ({ ...p, current: e.target.value }))}
              className="mt-1 bg-secondary border-border text-sm"
              placeholder="••••••••"
            />
          </div>
          <div>
            <Label className="text-xs">New Password</Label>
            <Input
              type="password"
              value={pwdForm.next}
              onChange={(e) => setPwdForm((p) => ({ ...p, next: e.target.value }))}
              className="mt-1 bg-secondary border-border text-sm"
              placeholder="Min 8 chars with upper, number, symbol"
            />
          </div>
          <div>
            <Label className="text-xs">Confirm New Password</Label>
            <Input
              type="password"
              value={pwdForm.confirm}
              onChange={(e) => setPwdForm((p) => ({ ...p, confirm: e.target.value }))}
              className="mt-1 bg-secondary border-border text-sm"
              placeholder="••••••••"
            />
          </div>
          <Button
            onClick={changePassword}
            disabled={loading || !pwdForm.current || !pwdForm.next}
            className="bg-primary hover:bg-primary/90"
            size="sm"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
            Update Password
          </Button>
        </div>
      </div>

      {/* Thresholds */}
      <div className="card-glass rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-4 h-4 text-amber-400" />
          <p className="text-sm font-semibold">Default Alert Thresholds</p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
          {[
            ["Daily Cost Alert", "$10.00"],
            ["Monthly Cost Alert", "$100.00"],
            ["P95 Latency Alert", "3000ms"],
            ["Error Rate Alert", "5%"],
            ["Injection Score Alert", "0.7"],
            ["Hallucination Rate Alert", "15%"],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between p-2.5 bg-secondary/40 rounded-lg">
              <span>{k}</span>
              <span className="font-mono font-semibold text-foreground">{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Security */}
      <div className="card-glass rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-emerald-400" />
          <p className="text-sm font-semibold">Security Settings</p>
        </div>
        <div className="space-y-2 text-xs text-muted-foreground">
          <div className="flex justify-between p-2.5 bg-secondary/40 rounded-lg">
            <span>JWT Token Expiry</span>
            <span className="font-mono font-semibold text-foreground">30 minutes</span>
          </div>
          <div className="flex justify-between p-2.5 bg-secondary/40 rounded-lg">
            <span>Refresh Token Expiry</span>
            <span className="font-mono font-semibold text-foreground">7 days</span>
          </div>
          <div className="flex justify-between p-2.5 bg-secondary/40 rounded-lg">
            <span>Rate Limit</span>
            <span className="font-mono font-semibold text-foreground">60/min · 1000/hr</span>
          </div>
          <div className="flex justify-between p-2.5 bg-secondary/40 rounded-lg">
            <span>Two-Factor Auth</span>
            <span className="font-mono font-semibold text-amber-400">Coming Soon</span>
          </div>
        </div>
      </div>
    </div>
  );
}
