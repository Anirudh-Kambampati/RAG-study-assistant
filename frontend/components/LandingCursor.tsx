"use client";

import { useEffect, useRef, useState } from "react";

const TRAIL_LENGTH = 8;
// Lead elements (star/ring/glow) lerp fastest-to-slowest in that order,
// trail dots continue the same curve so the whole thing reads as one
// decelerating chain rather than two separately-tuned systems.
const STAR_LERP = 0.38;
const RING_LERP = 0.26;
const GLOW_LERP = 0.14;
const TRAIL_LERP = Array.from({ length: TRAIL_LENGTH }, (_, i) => 0.22 * Math.pow(0.85, i));

type Point = { x: number; y: number };

/**
 * Custom animated cursor for the landing page only — ported from the Aether
 * project's Cursor.tsx, re-implemented against this app's actual stack
 * (plain CSS + a single requestAnimationFrame loop) instead of pulling in
 * framer-motion/Tailwind, neither of which this project depends on.
 *
 * Position is written every frame as CSS custom properties (--x/--y) rather
 * than directly as `transform`, so it never fights the scale/rotate/opacity
 * React sets declaratively on the same elements — the stylesheet composes
 * both into one `transform` via var(...).
 *
 * Mounted only on the landing page (see app/page.tsx); toggling the native
 * cursor off is scoped to exactly its own mount lifetime via a body class,
 * so other pages are unaffected. Disabled outright for touch input and
 * under reduced-motion, in which case the native cursor is left alone.
 */
export default function LandingCursor() {
  const [enabled, setEnabled] = useState(false);
  const [visible, setVisible] = useState(false);
  const [hovering, setHovering] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [bursts, setBursts] = useState<{ id: number; x: number; y: number }[]>([]);

  const mouseRef = useRef<Point>({ x: 0, y: 0 });
  const starRef = useRef<HTMLImageElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const trailRefs = useRef<(HTMLImageElement | null)[]>([]);
  const positions = useRef<Point[]>(Array.from({ length: TRAIL_LENGTH }, () => ({ x: 0, y: 0 })));
  const starPos = useRef<Point>({ x: 0, y: 0 });
  const ringPos = useRef<Point>({ x: 0, y: 0 });
  const glowPos = useRef<Point>({ x: 0, y: 0 });
  const rafRef = useRef<number | undefined>(undefined);
  const burstIdRef = useRef(0);

  useEffect(() => {
    const coarsePointer = window.matchMedia?.("(pointer: coarse)").matches;
    const reduceMotion =
      document.documentElement.classList.contains("reduce-motion") ||
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (coarsePointer || reduceMotion) return;

    setEnabled(true);
    document.body.classList.add("landing-custom-cursor");

    const move = (e: MouseEvent) => {
      setVisible(true);
      mouseRef.current = { x: e.clientX, y: e.clientY };
      const target = e.target as HTMLElement;
      setHovering(!!target.closest("button, a, input, textarea, [role='button']"));
    };
    const leave = () => setVisible(false);
    const down = (e: MouseEvent) => {
      setClicked(true);
      const id = burstIdRef.current++;
      setBursts((b) => [...b, { id, x: e.clientX, y: e.clientY }]);
      window.setTimeout(() => setBursts((b) => b.filter((burst) => burst.id !== id)), 380);
    };
    const up = () => setClicked(false);

    const setPos = (el: HTMLElement | null, pos: Point, offset: number) => {
      if (!el) return;
      el.style.setProperty("--x", `${pos.x - offset}px`);
      el.style.setProperty("--y", `${pos.y - offset}px`);
    };

    const tick = () => {
      const m = mouseRef.current;

      starPos.current.x += (m.x - starPos.current.x) * STAR_LERP;
      starPos.current.y += (m.y - starPos.current.y) * STAR_LERP;
      setPos(starRef.current, starPos.current, 10);

      ringPos.current.x += (m.x - ringPos.current.x) * RING_LERP;
      ringPos.current.y += (m.y - ringPos.current.y) * RING_LERP;
      setPos(ringRef.current, ringPos.current, 18);

      glowPos.current.x += (m.x - glowPos.current.x) * GLOW_LERP;
      glowPos.current.y += (m.y - glowPos.current.y) * GLOW_LERP;
      setPos(glowRef.current, glowPos.current, 28);

      const pos = positions.current;
      pos[0].x += (starPos.current.x - pos[0].x) * TRAIL_LERP[0];
      pos[0].y += (starPos.current.y - pos[0].y) * TRAIL_LERP[0];
      setPos(trailRefs.current[0], pos[0], 8);
      for (let i = 1; i < TRAIL_LENGTH; i++) {
        pos[i].x += (pos[i - 1].x - pos[i].x) * TRAIL_LERP[i];
        pos[i].y += (pos[i - 1].y - pos[i].y) * TRAIL_LERP[i];
        setPos(trailRefs.current[i], pos[i], 8);
      }

      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);

    window.addEventListener("mousemove", move);
    window.addEventListener("mouseleave", leave);
    window.addEventListener("mousedown", down);
    window.addEventListener("mouseup", up);

    return () => {
      document.body.classList.remove("landing-custom-cursor");
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseleave", leave);
      window.removeEventListener("mousedown", down);
      window.removeEventListener("mouseup", up);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  if (!enabled) return null;

  const cssVar = (props: Record<string, string | number>) => props as React.CSSProperties;

  return (
    <div aria-hidden="true">
      {Array.from({ length: TRAIL_LENGTH }, (_, i) => (
        <img
          key={i}
          ref={(el) => {
            trailRefs.current[i] = el;
          }}
          src="/cursor/star.svg"
          alt=""
          draggable={false}
          className="landing-cursor-trail"
          style={cssVar({ opacity: visible ? 1 - i / TRAIL_LENGTH : 0, "--s": 1 - i * 0.07 })}
        />
      ))}

      <div
        ref={glowRef}
        className="landing-cursor-glow"
        style={cssVar({ opacity: visible ? (hovering ? 0.5 : 0.25) : 0 })}
      />

      <div
        ref={ringRef}
        className="landing-cursor-ring"
        style={cssVar({ opacity: visible ? 1 : 0, "--s": clicked ? 0.8 : hovering ? 1.4 : 1 })}
      />

      <img
        ref={starRef}
        src="/cursor/star.svg"
        alt=""
        draggable={false}
        className="landing-cursor-star"
        style={cssVar({
          opacity: visible ? 1 : 0,
          "--s": clicked ? 0.85 : hovering ? 1.25 : 1,
          "--r": `${hovering ? 20 : 0}deg`,
        })}
      />

      {bursts.map((b) => (
        <div key={b.id} className="landing-cursor-burst" style={{ left: b.x - 20, top: b.y - 20 }} />
      ))}
    </div>
  );
}
