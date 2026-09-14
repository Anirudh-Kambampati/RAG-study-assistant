"use client";

import { useEffect, useRef, useState } from "react";

export type LandingScene = {
  id: string;
  label: string;
};

/**
 * Subtle right-side scroll indicator for the landing page's snap sections.
 * Active section is tracked via IntersectionObserver (not scroll listeners),
 * and clicking a dot scrolls the matching section into view — instantly
 * under prefers-reduced-motion, smoothly otherwise.
 */
export default function SectionDots({ scenes }: { scenes: LandingScene[] }) {
  const [active, setActive] = useState(scenes[0]?.id ?? "");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const elements = scenes
      .map((s) => document.getElementById(s.id))
      .filter((el): el is HTMLElement => el !== null);
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(visible.target.id);
      },
      { threshold: [0.5, 0.6, 0.7, 0.8] }
    );
    observerRef.current = observer;
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [scenes]);

  function goTo(id: string) {
    const el = document.getElementById(id);
    if (!el) return;
    const reduceMotion =
      typeof window !== "undefined" &&
      (document.documentElement.classList.contains("reduce-motion") ||
        window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
    el.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  }

  return (
    <nav className="landing-dots" aria-label="Page sections">
      {scenes.map((s) => (
        <button
          key={s.id}
          type="button"
          className={`landing-dot ${active === s.id ? "active" : ""}`}
          aria-label={`Go to ${s.label}`}
          aria-current={active === s.id ? "true" : undefined}
          onClick={() => goTo(s.id)}
        />
      ))}
    </nav>
  );
}
