"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { useSettings } from "@/components/SettingsProvider";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // Subscribe so the shell re-renders on settings changes (theme is applied
  // directly to <html> by the provider).
  useSettings();

  const activeDocId = pathname?.startsWith("/chat/")
    ? decodeURIComponent(pathname.slice("/chat/".length))
    : undefined;

  return (
    <div className="app-shell">
      <Sidebar activeDocId={activeDocId} />
      <div className="main-area">{children}</div>
    </div>
  );
}
