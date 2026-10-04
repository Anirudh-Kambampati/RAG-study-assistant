"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { fetchChats, deleteChat, type ChatMap } from "@/lib/api";
import { EditIcon, FileIcon, GearIcon, LogOutIcon, MenuIcon, TrashIcon } from "@/components/icons";
import { useAuth } from "@/components/AuthProvider";

export default function Sidebar({ activeDocId }: { activeDocId?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(true);
  const [chats, setChats] = useState<ChatMap>({});

  const refreshChats = useCallback(async () => {
    try {
      setChats(await fetchChats());
    } catch {
      // sidebar degrades gracefully when backend is down
    }
  }, []);

  // Reload history on mount, active-chat change, and sidebar (re)open
  useEffect(() => {
    refreshChats();
  }, [refreshChats, activeDocId, open]);

  async function handleDelete(docId: string) {
    if (!confirm(`Delete chat "${docId}"? Its indexed document is kept on disk.`)) return;
    await deleteChat(docId);
    await refreshChats();
    if (docId === activeDocId) router.push("/dashboard");
  }

  async function handleLogout() {
    await logout();
    // Hard navigation, not router.push: the session cookie was just cleared
    // by a plain fetch() (not a router-driven action), which the client-side
    // router cache doesn't know about. router.push can then reuse a stale
    // cached decision from while the cookie was still present and bounce
    // back to /dashboard instead of landing on /login. A full page load
    // guarantees the middleware re-evaluates with the now-cleared cookie.
    window.location.href = "/login";
  }

  const onSettingsPage = pathname === "/settings";
  const onDashboard = pathname === "/dashboard";

  return (
    <aside className={`sidebar ${open ? "open" : "collapsed"}`}>
      <div className="sidebar-top">
        <button
          className="sidebar-toggle"
          onClick={() => setOpen(!open)}
          aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
          aria-expanded={open}
        >
          <MenuIcon />
        </button>
        {open && (
          <span className="sidebar-brand">
            <FileIcon size={17} />
            Metis
          </span>
        )}
      </div>

      <Link
        href="/dashboard"
        className={`new-chat-btn ${onDashboard ? "active" : ""}`}
        title="New chat"
      >
        <span className="icon">
          <EditIcon />
        </span>
        {open && <span>New chat</span>}
      </Link>

      {open && <div className="sidebar-section-label">Chats</div>}
      <nav className="chat-history" aria-label="Chat history">
        {open && Object.keys(chats).length === 0 && (
          <p className="sidebar-empty">No chats yet</p>
        )}
        {Object.keys(chats).map((docId) => {
          const isActive = docId === activeDocId;
          return (
            <div key={docId} className={`history-item ${isActive ? "active" : ""}`}>
              <Link
                href={`/chat/${encodeURIComponent(docId)}`}
                className="history-link"
                title={docId}
                aria-current={isActive ? "page" : undefined}
              >
                <span className="history-icon" aria-hidden="true">
                  <FileIcon size={16} />
                </span>
                {open && (
                  <span className="history-text">
                    <span className="history-name">{docId}</span>
                    <span className="history-meta">Document chat</span>
                  </span>
                )}
              </Link>
              {open && (
                <button
                  className="history-delete"
                  onClick={() => handleDelete(docId)}
                  aria-label={`Delete ${docId}`}
                >
                  <TrashIcon size={15} />
                </button>
              )}
            </div>
          );
        })}
      </nav>

      <Link
        href="/settings"
        className={`sidebar-settings ${onSettingsPage ? "active" : ""}`}
        title="Settings"
      >
        <span className="icon">
          <GearIcon />
        </span>
        {open && <span>Settings</span>}
      </Link>

      {user && (
        <button className="sidebar-user" onClick={handleLogout} title={`Sign out (${user.email})`}>
          <span className="sidebar-user-avatar" aria-hidden="true">
            {user.name.trim().charAt(0).toUpperCase() || "?"}
          </span>
          {open && (
            <span className="sidebar-user-text">
              <span className="sidebar-user-name">{user.name}</span>
              <span className="sidebar-user-action">
                <LogOutIcon size={12} /> Sign out
              </span>
            </span>
          )}
        </button>
      )}
    </aside>
  );
}
