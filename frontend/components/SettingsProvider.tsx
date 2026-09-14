"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  applyAppearance,
  effectiveK,
  loadSettings,
  resetSettings,
  saveSettings,
  sanitize,
  type Settings,
} from "@/lib/settings";
import { useAuth } from "@/components/AuthProvider";

type SettingsContextValue = {
  settings: Settings;
  /** Update one or more settings, persist and re-apply appearance immediately. */
  update: (patch: Partial<Settings>) => void;
  /** Restore defaults. */
  reset: () => void;
  /** Effective chunks-per-query for the current search depth. */
  effectiveK: number;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);

/**
 * localStorage remains the fast, always-available source (works signed out,
 * survives a slow/offline backend). Once a user is known, we additionally:
 *  - hydrate once from their server-stored settings (last device wins over
 *    whatever this browser had cached, since the server is the
 *    cross-device source of truth once you're signed in), then
 *  - fire-and-forget PUT every change to /api/settings, scoped to that
 *    user by the session cookie — never trusted from the client otherwise.
 */
export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<Settings>(() => loadSettings());
  const { user, loading: authLoading } = useAuth();
  const hydratedForUser = useRef<string | null>(null);

  useEffect(() => {
    return applyAppearance(settings);
  }, [settings]);

  useEffect(() => {
    if (authLoading || !user || hydratedForUser.current === user.id) return;
    hydratedForUser.current = user.id;
    (async () => {
      try {
        const res = await fetch("/api/settings", { cache: "no-store" });
        if (!res.ok) return;
        const remote = await res.json();
        if (remote && Object.keys(remote).length > 0) {
          const next = sanitize(remote);
          saveSettings(next);
          setSettings(next);
        }
      } catch {
        // offline/unreachable backend: keep whatever localStorage already had
      }
    })();
  }, [authLoading, user]);

  const syncToServer = useCallback((next: Settings) => {
    fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(next),
    }).catch(() => {
      // best-effort: the local copy already saved, this is just cross-device sync
    });
  }, []);

  const update = useCallback(
    (patch: Partial<Settings>) => {
      setSettings((prev) => {
        const next = { ...prev, ...patch };
        saveSettings(next);
        if (user) syncToServer(next);
        return next;
      });
    },
    [user, syncToServer]
  );

  const reset = useCallback(() => {
    const next = resetSettings();
    setSettings(next);
    if (user) syncToServer(next);
  }, [user, syncToServer]);

  const value = useMemo<SettingsContextValue>(
    () => ({ settings, update, reset, effectiveK: effectiveK(settings) }),
    [settings, update, reset]
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
