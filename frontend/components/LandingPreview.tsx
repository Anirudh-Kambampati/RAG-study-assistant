import type { ReactNode } from "react";
import { ArrowUpIcon, EditIcon, FileIcon, PaperclipIcon } from "@/components/icons";

/**
 * A static, non-interactive reproduction of the real METIS chat UI
 * (Sidebar + chat header + message bubbles + sources + composer), reusing
 * the same visual language as components/Sidebar.tsx and
 * app/(app)/chat/[docId]/page.tsx. This is illustrative content over an
 * existing capability, not an invented feature — no functionality here is
 * wired up (it's aria-hidden and non-interactive by design).
 */
type PreviewSource = { label: string };

export default function LandingPreview({
  variant = "hero",
  showSources = false,
  docTitle = "Biology_Ch4.pdf",
  historyItems = ["Biology_Ch4.pdf", "Lecture_Notes.docx"],
  question = "What's the difference between mitosis and meiosis?",
  answer = (
    <>
      <strong>Mitosis</strong> produces two genetically identical diploid cells and is used for
      growth and repair. <strong>Meiosis</strong> produces four genetically distinct haploid
      cells and is used for sexual reproduction.
    </>
  ),
  modeTag = "Tutor mode",
  sources = [
    { label: '#1 · page 14 · "Mitosis is divided into..."' },
    { label: '#2 · page 16 · "Unlike mitosis, meiosis..."' },
  ],
}: {
  variant?: "hero" | "panel" | "dashboard";
  showSources?: boolean;
  docTitle?: string;
  historyItems?: string[];
  question?: ReactNode;
  answer?: ReactNode;
  modeTag?: string;
  sources?: PreviewSource[];
}) {
  const isDashboard = variant === "dashboard";

  return (
    <div className={`landing-preview landing-preview--${variant}`} aria-hidden="true">
      <div className="landing-preview-chrome">
        <span />
        <span />
        <span />
      </div>
      <div className="landing-preview-body">
        <aside className="landing-preview-sidebar">
          <div className="landing-preview-sidebar-brand">
            <FileIcon size={14} />
            Metis
          </div>
          <div className="landing-preview-newchat">
            <EditIcon size={13} />
            New chat
          </div>
          {historyItems.map((item, i) => (
            <div key={item} className={`landing-preview-history-item${i === 0 ? " active" : ""}`}>
              <FileIcon size={13} />
              {item}
            </div>
          ))}
        </aside>

        {isDashboard ? (
          <div className="landing-preview-main landing-preview-main--dashboard">
            <div className="landing-preview-dash-thread">
              <div className="landing-preview-bubble user">{question}</div>
              <div className="landing-preview-bubble assistant">
                {answer}
                <span className="landing-preview-mode-tag">{modeTag}</span>
              </div>
            </div>
            <div className="landing-preview-composer">
              <PaperclipIcon size={14} />
              <span>Ask something about this document…</span>
              <span className="landing-preview-send">
                <ArrowUpIcon size={13} />
              </span>
            </div>
          </div>
        ) : (
          <div className="landing-preview-main">
            <div className="landing-preview-chatheader">
              <FileIcon size={14} />
              {docTitle}
            </div>
            <div className="landing-preview-messages">
              <div className="landing-preview-bubble user">{question}</div>
              <div className="landing-preview-bubble assistant">
                {answer}
                <span className="landing-preview-mode-tag">{modeTag}</span>
              </div>
              {showSources && (
                <div className="landing-preview-sources">
                  <div className="landing-preview-sources-title">Sources</div>
                  {sources.map((s) => (
                    <div className="landing-preview-source-row" key={s.label}>
                      {s.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="landing-preview-composer">
              <PaperclipIcon size={14} />
              <span>Ask something about this document…</span>
              <span className="landing-preview-send">
                <ArrowUpIcon size={13} />
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
