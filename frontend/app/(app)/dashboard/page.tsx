"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createChat } from "@/lib/api";
import { ArrowUpIcon, FileIcon, PaperclipIcon } from "@/components/icons";

const ALLOWED = ["pdf", "docx", "pptx", "txt"];
const ACCEPT = ALLOWED.map((ext) => `.${ext}`).join(",");

export default function Home() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [stage, setStage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [backendDown, setBackendDown] = useState(false);
  const [typedGreeting, setTypedGreeting] = useState("");

  const GREETING = "What can I help you with today?";

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setTypedGreeting(GREETING.slice(0, i));
      if (i >= GREETING.length) clearInterval(timer);
    }, 22);
    return () => clearInterval(timer);
  }, []);

  async function handleFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported format: .${ext}. Allowed: ${ALLOWED.join(", ")}`);
      return;
    }
    setError(null);
    setUploading(true);
    try {
      setStage("Indexing document (one-time process)…");
      const docId = await createChat(file.name, file);
      router.push(`/chat/${encodeURIComponent(docId)}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setError(msg);
      setBackendDown(/fetch|network/i.test(msg));
      setStage("");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="home-page">
      <div className="hero">
        <h1 className="hero-title">
          <span className="hero-icon">
            <FileIcon size={26} />
          </span>
          Metis
        </h1>
        <p className="hero-tagline">Your RAG-powered study assistant — chat with your own documents.</p>
        <p className="hero-greeting">{typedGreeting}</p>

        <form
          className="home-composer"
          onSubmit={(e) => {
            e.preventDefault();
            fileInputRef.current?.click();
          }}
        >
          <button
            type="submit"
            className="attach-btn"
            disabled={uploading}
            title="Attach a document (PDF, DOCX, PPTX, TXT)"
          >
            <PaperclipIcon />
          </button>
          <input
            className="home-input"
            placeholder={
              uploading ? stage || "Working…" : "Attach a document to start a chat…"
            }
            readOnly
            onClick={() => fileInputRef.current?.click()}
          />
          <button type="submit" className="send-btn" disabled={uploading}>
            {uploading ? "…" : <ArrowUpIcon />}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              e.target.value = "";
            }}
          />
        </form>

        {error && (
          <p className="error">
            {error}
            {backendDown && (
              <>
                {" — "}
                <span className="muted">
                  is the backend running? (uvicorn api.main:app --reload)
                </span>
              </>
            )}
          </p>
        )}
        {!error && (
          <p className="home-hint muted">
            Attach a PDF, DOCX, PPTX, or TXT — it gets indexed once, then you can chat with it.
          </p>
        )}
        {uploading && (
          <div className="upload-progress">
            <div className="spinner" /> <span>{stage}</span>
          </div>
        )}
      </div>
    </main>
  );
}
