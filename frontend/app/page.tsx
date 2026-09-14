"use client";

import Link from "next/link";
import {
  ArrowDownIcon,
  FileIcon,
  GithubIcon,
  MailIcon,
  MessageCircleIcon,
  ModeIcon,
  PlanetRingIcon,
  ShieldIcon,
} from "@/components/icons";
import LandingPreview from "@/components/LandingPreview";
import SectionDots, { type LandingScene } from "@/components/SectionDots";
import { ASSISTANT_MODE_INFO, ASSISTANT_MODE_OPTIONS } from "@/lib/settings";

const SCENES: LandingScene[] = [
  { id: "hero", label: "Home" },
  { id: "workspace", label: "The Workspace" },
  { id: "study-modes", label: "Study Modes" },
  { id: "grounded", label: "Grounded Learning" },
];

const GROUNDED_POINTS = [
  {
    strong: "Answers grounded in your document.",
    text: "Metis answers from what you uploaded, and can tell you plainly when your document doesn't cover something.",
  },
  {
    strong: "Source references.",
    text: "Every answer can show the passages it drew from, so you can check it against the original text.",
  },
  {
    strong: "Conversation context.",
    text: "Follow-up questions build on what you already asked, within the same document chat.",
  },
  {
    strong: "Tune it to how you study.",
    text: "Response style, format, and behavior — explain terms, give examples, highlight key points — are all adjustable in Settings.",
  },
];

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function LandingPage() {
  return (
    <div className="landing">
      <div className="landing-cosmos" aria-hidden="true">
        <div className="landing-stars" />
      </div>

      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link href="/" className="landing-brand">
            <span className="landing-brand-mark">
              <FileIcon size={16} />
            </span>
            Metis
          </Link>
          <nav className="landing-nav-links" aria-label="Page sections">
            <button type="button" onClick={() => scrollToId("workspace")}>
              Features
            </button>
            <button type="button" onClick={() => scrollToId("study-modes")}>
              Study Modes
            </button>
            <button type="button" onClick={() => scrollToId("grounded")}>
              About
            </button>
          </nav>
          <div className="landing-nav-actions">
            <Link href="/login" className="landing-nav-login">
              Log in
            </Link>
            <Link href="/signup" className="landing-nav-cta">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <SectionDots scenes={SCENES} />

      {/* ============================================================ 01 — Hero */}
      <section id="hero" className="landing-scene">
        <div className="landing-scene-inner landing-hero">
          <span className="landing-hero-wordmark">
            <span className="landing-hero-mark">
              <PlanetRingIcon size={28} />
            </span>
            METIS
          </span>

          <h1 className="landing-hero-title">Turn your documents into understanding.</h1>
          <p className="landing-hero-tagline">A study workspace built around one document at a time.</p>
          <p className="landing-hero-sub">
            Upload what you&apos;re learning from, ask questions in your own words, and get answers
            grounded in your own material — shaped by the way you actually study.
          </p>

          <div className="landing-hero-actions">
            <Link href="/signup" className="landing-btn-primary">
              Start Learning
            </Link>
            <button type="button" className="landing-btn-secondary" onClick={() => scrollToId("workspace")}>
              See the Workspace
            </button>
          </div>
        </div>

        <button
          type="button"
          className="landing-scroll-cue"
          onClick={() => scrollToId("workspace")}
          aria-label="Scroll to next section"
        >
          <span className="landing-scroll-cue-icon">
            <ArrowDownIcon size={16} />
          </span>
          Scroll
        </button>
      </section>

      {/* ======================================================= 02 — Workspace */}
      <section id="workspace" className="landing-scene">
        <div className="landing-scene-inner landing-workspace">
          <div className="landing-workspace-text">
            <span className="landing-eyebrow">The Workspace</span>
            <h2 className="landing-scene-title landing-scene-title-spaced">
              One document. A real conversation.
            </h2>
            <p className="landing-scene-sub">
              Every chat lives next to the document it belongs to. Ask a question, get a grounded
              answer, and keep going — the same interface you&apos;ll actually use.
            </p>
            <ul className="landing-workspace-points">
              <li>
                <span className="landing-point-icon">
                  <FileIcon size={15} />
                </span>
                Upload a PDF, DOCX, PPTX, or TXT and it&apos;s indexed for chat in one step.
              </li>
              <li>
                <span className="landing-point-icon">
                  <MessageCircleIcon size={15} />
                </span>
                Ask follow-up questions naturally, within the same document&apos;s conversation.
              </li>
              <li>
                <span className="landing-point-icon">
                  <ShieldIcon size={15} />
                </span>
                Every document and chat is scoped to your account.
              </li>
            </ul>
          </div>
          <LandingPreview variant="dashboard" />
        </div>
      </section>

      {/* ==================================================== 03 — Study modes */}
      <section id="study-modes" className="landing-scene">
        <div className="landing-scene-inner landing-scene-centered">
          <span className="landing-eyebrow">Study Modes</span>
          <h2 className="landing-scene-title landing-scene-title-spaced">
            One document, four ways to study it.
          </h2>
          <p className="landing-scene-sub landing-scene-sub-centered">
            Switch modes anytime in Settings — mid-conversation, if you like.
          </p>
          <div className="landing-modes-grid landing-modes-grid--2x2">
            {ASSISTANT_MODE_OPTIONS.map((m) => {
              const info = ASSISTANT_MODE_INFO[m];
              return (
                <div className="landing-mode-card" key={m}>
                  <span className="landing-mode-icon">
                    <ModeIcon name={info.icon} size={18} />
                  </span>
                  <h3>{info.label}</h3>
                  <p>{info.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ==================================================== 05 — Grounded learning */}
      <section id="grounded" className="landing-scene">
        <div className="landing-scene-inner landing-scene-centered landing-scene-inner--split">
          <div className="landing-grounded-main">
            <span className="landing-eyebrow">Grounded Learning</span>
            <h2 className="landing-scene-title landing-scene-title-spaced">
              Your workspace, answering from your material.
            </h2>
            <ul className="landing-grounded-list landing-grounded-list--centered">
              {GROUNDED_POINTS.map((p) => (
                <li key={p.strong}>
                  <strong>{p.strong}</strong> {p.text}
                </li>
              ))}
            </ul>
          </div>

          <footer className="landing-footer landing-grounded-footer">
            <div className="landing-footer-contact">
              <a href="mailto:anirudhkambampati@gmail.com">
                <MailIcon size={15} />
                anirudhkambampati@gmail.com
              </a>
              <a href="https://github.com/anirudh-kambampati" target="_blank" rel="noopener noreferrer">
                <GithubIcon size={15} />
                github.com/anirudh-kambampati
              </a>
            </div>
            <button type="button" className="landing-footer-btn" onClick={() => scrollToId("hero")}>
              Back to top
            </button>
            <span className="landing-footer-credit">Designed and developed with ❤️ by Anirudh Kambampati</span>
          </footer>
        </div>
      </section>
    </div>
  );
}
