"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fetchChats, sendQuery, type AssistantMessage, type ChatMessage, type QuerySource } from "@/lib/api";
import { useSettings } from "@/components/SettingsProvider";
import { ASSISTANT_MODE_INFO, effectiveK } from "@/lib/settings";
import {
  ArrowLeftIcon,
  ArrowUpIcon,
  BookOpenIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  FileIcon,
  ModeIcon,
} from "@/components/icons";

const EMPTY_STATE_COPY: Record<string, string> = {
  "quick-answer": "Get concise answers from your document.",
  tutor: "Learn the concepts step by step.",
  "exam-prep": "Focus on what matters for your exam.",
  research: "Explore the document's concepts in depth.",
};

const STARTER_PROMPTS = [
  "Summarize this document",
  "Explain the main concepts",
  "What should I study for an exam?",
  "Find the key topics",
];

/** Turn "[1]", "[2]" citation markers the model was instructed to emit into
 * markdown links (`[1](#cite-1)`) so react-markdown parses them as real
 * link nodes we can intercept and swap for a hoverable CitationMarker. */
function citationizeContent(content: string, sourceCount: number): string {
  if (!sourceCount) return content;
  // The model is instructed to use plain ASCII brackets, but LLMs occasionally
  // substitute full-width CJK brackets (e.g. "【1】") or add a thin space before
  // the marker — normalize those before matching so citations still render.
  const normalized = content.replace(/[【\[]\s*(\d+)\s*[】\]]/g, "[$1]");
  return normalized.replace(/\[(\d+)\](?!\()/g, (match, numStr: string) => {
    const num = parseInt(numStr, 10);
    return num >= 1 && num <= sourceCount ? `[${num}](#cite-${num})` : match;
  });
}

function CitationMarker({ source }: { source: QuerySource }) {
  const [open, setOpen] = useState(false);

  return (
    <span
      className="citation-marker"
      tabIndex={0}
      role="button"
      aria-label={`Source ${source.rank}${source.page !== null ? `, page ${source.page}` : ""}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {source.rank}
      {open && (
        <span className="citation-card" role="tooltip">
          <span className="citation-card-header">
            <FileIcon size={12} />
            {source.title ?? "Source"}
            {source.page !== null && <span className="citation-card-page">page {source.page}</span>}
          </span>
          <p className="citation-card-snippet">{source.snippet}</p>
        </span>
      )}
    </span>
  );
}

function SourcesPanel({ sources }: { sources: QuerySource[] }) {
  const [open, setOpen] = useState(false);
  if (sources.length === 0) return null;

  return (
    <div className="sources">
      <button className="sources-toggle" onClick={() => setOpen(!open)}>
        {open ? <ChevronDownIcon size={13} /> : <ChevronRightIcon size={13} />}
        Sources ({sources.length})
      </button>
      {open && (
        <ol className="sources-list">
          {sources.map((s) => (
            <li key={s.rank} id={`source-${s.rank}`}>
              <span className="source-rank">#{s.rank}</span>
              {s.page !== null && <span className="source-page"> page {s.page}</span>}
              {s.score !== null && (
                <span className="source-score"> score {s.score.toFixed(3)}</span>
              )}
              <p className="source-snippet">{s.snippet}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default function ChatPage() {
  const params = useParams<{ docId: string }>();
  const docId = decodeURIComponent(params.docId);

  const [messages, setMessages] = useState<(ChatMessage & { sources?: QuerySource[] })[] | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { settings } = useSettings();

  const loadChat = useCallback(async () => {
    try {
      const chats = await fetchChats();
      const chat = chats[docId];
      if (!chat) {
        setNotFound(true);
        return;
      }
      setMessages(chat.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chat");
      setMessages([]);
    }
  }, [docId]);

  useEffect(() => {
    loadChat();
  }, [loadChat]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  async function submitQuery(query: string) {
    if (!query || thinking) return;

    setInput("");
    setError(null);
    setThinking(true);
    setMessages((prev) => [...(prev ?? []), { role: "user", content: query }]);

    try {
      const reply: AssistantMessage = await sendQuery(docId, query, {
        k: effectiveK(settings),
        style: settings.responseStyle,
        format: settings.responseFormat,
        assistantMode: settings.assistantMode,
        groundingMode: settings.groundingMode,
        explainTerms: settings.explainTerms,
        giveExamples: settings.giveExamples,
        highlightKeyPoints: settings.highlightKeyPoints,
        relatedConcepts: settings.relatedConcepts,
        askClarifyingQuestions: settings.askClarifyingQuestions,
      });
      setMessages((prev) => [...(prev ?? []), { role: "assistant", content: reply.content, sources: reply.sources }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "I couldn't generate an answer right now.");
      setMessages((prev) => prev?.slice(0, -1) ?? prev);
      setInput(query);
    } finally {
      setThinking(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await submitQuery(input.trim());
  }

  function handleRetry() {
    submitQuery(input.trim());
  }

  if (notFound) {
    return (
      <main className="chat-page">
        <div className="messages">
          <p className="error">Chat not found.</p>
          <Link href="/" className="primary-link">
            <ArrowLeftIcon size={14} /> Start a new chat
          </Link>
        </div>
      </main>
    );
  }

  const modeInfo = ASSISTANT_MODE_INFO[settings.assistantMode];

  return (
    <main className="chat-page">
      <div className="chat-header">
        <div className="chat-header-inner">
          <div className="chat-header-main">
            <span className="chat-header-icon" aria-hidden="true">
              <FileIcon size={18} />
            </span>
            <div className="chat-header-text">
              <h1 className="chat-title" title={docId}>
                {docId}
              </h1>
              <p className="chat-subtitle">Ask questions about this document</p>
            </div>
          </div>
          <div className="mode-indicator" title={modeInfo.description}>
            <span aria-hidden="true">
              <ModeIcon name={modeInfo.icon} size={14} />
            </span>
            <span>{modeInfo.label}</span>
          </div>
        </div>
      </div>

      <div className="messages">
        {messages === null ? (
          <p className="muted">Loading…</p>
        ) : messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-icon" aria-hidden="true">
              <BookOpenIcon />
            </div>
            <h2 className="empty-title">Understand your document</h2>
            <p className="empty-subtitle">{EMPTY_STATE_COPY[settings.assistantMode]}</p>
            <div className="suggestion-grid">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="suggestion-chip"
                  onClick={() => submitQuery(prompt)}
                  disabled={thinking}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`bubble ${msg.role}`}>
              {msg.role === "assistant" ? (
                <>
                  <div className="markdown">
                    <Markdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ href, children }) => {
                          if (href?.startsWith("#cite-")) {
                            const source = msg.sources?.[parseInt(href.slice(6), 10) - 1];
                            if (source) return <CitationMarker source={source} />;
                          }
                          return (
                            <a href={href} target="_blank" rel="noopener noreferrer">
                              {children}
                            </a>
                          );
                        },
                      }}
                    >
                      {citationizeContent(msg.content, msg.sources?.length ?? 0)}
                    </Markdown>
                  </div>
                  {settings.showSources && msg.sources && <SourcesPanel sources={msg.sources} />}
                </>
              ) : (
                msg.content
              )}
            </div>
          ))
        )}
        {thinking && (
          <div className="bubble assistant thinking">
            <span className="thinking-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            <span>Thinking…</span>
          </div>
        )}
        {error && (
          <div className="error-card" role="alert">
            <p className="error-title">Something went wrong</p>
            <p className="error-detail">{error}</p>
            <button type="button" className="error-retry" onClick={handleRetry} disabled={!input.trim() || thinking}>
              Retry
            </button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="composer">
        <div className="composer-row">
          <div className="composer-inner">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something about this document…"
              aria-label="Ask a question about this document"
              disabled={thinking}
              autoFocus
            />
            <button
              type="submit"
              className="send-btn"
              aria-label="Send message"
              disabled={!input.trim() || thinking}
            >
              <ArrowUpIcon />
            </button>
          </div>
        </div>
      </form>
    </main>
  );
}
