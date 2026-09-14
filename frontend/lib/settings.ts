"use client";

import type { ModeIconName } from "@/components/icons";

export type ThemeSetting = "system" | "light" | "dark";
export type AccentColor = "blue" | "purple" | "green" | "orange" | "pink" | "red";
export type FontSize = "small" | "medium" | "large";
export type Density = "compact" | "comfortable" | "spacious";
export type MessageStyle = "bubbles" | "minimal";
export type ResponseStyle = "concise" | "balanced" | "detailed" | "beginner";
export type ResponseFormat = "paragraphs" | "bullets" | "step-by-step";
export type SearchDepth = "fast" | "balanced" | "thorough";
export type AssistantMode = "quick-answer" | "tutor" | "exam-prep" | "research";
export type GroundingMode = "strict-documents" | "documents-general";

export type Settings = {
  version: number;

  // Appearance
  theme: ThemeSetting;
  accentColor: AccentColor;
  fontSize: FontSize;
  density: Density;
  messageStyle: MessageStyle;
  background: "solid" | "gradient";

  // Accessibility
  reducedMotion: boolean;
  highContrast: boolean;

  // Chat
  responseStyle: ResponseStyle;
  responseFormat: ResponseFormat;
  showSources: boolean;

  // Knowledge
  searchDepth: SearchDepth;
  retrievalK: number;
  groundingMode: GroundingMode;

  // Assistant
  assistantMode: AssistantMode;
  explainTerms: boolean;
  giveExamples: boolean;
  highlightKeyPoints: boolean;
  relatedConcepts: boolean;
  askClarifyingQuestions: boolean;
};

export const SETTINGS_VERSION = 1;

export const DEFAULT_SETTINGS: Settings = {
  version: SETTINGS_VERSION,

  theme: "dark",
  accentColor: "red",
  fontSize: "medium",
  density: "comfortable",
  messageStyle: "bubbles",
  background: "solid",

  reducedMotion: false,
  highContrast: false,

  responseStyle: "balanced",
  responseFormat: "paragraphs",
  showSources: true,

  searchDepth: "balanced",
  retrievalK: 7,
  groundingMode: "strict-documents",

  assistantMode: "tutor",
  explainTerms: false,
  giveExamples: false,
  highlightKeyPoints: false,
  relatedConcepts: false,
  askClarifyingQuestions: false,
};

/** Depth preset -> chunks retrieved per query (server clamps to 1..16). */
export const DEPTH_K: Record<SearchDepth, number> = {
  fast: 4,
  balanced: 7,
  thorough: 12,
};

export const ACCENT_OPTIONS: AccentColor[] = ["blue", "purple", "green", "orange", "pink", "red"];

export const DEPTH_INFO: Record<SearchDepth, { label: string; description: string }> = {
  fast: { label: "Fast", description: "Find a few highly relevant passages quickly." },
  balanced: { label: "Balanced", description: "Search enough context for a reliable answer." },
  thorough: { label: "Thorough", description: "Search more context for complex questions." },
};

export const ASSISTANT_MODE_INFO: Record<
  AssistantMode,
  { label: string; icon: ModeIconName; description: string }
> = {
  "quick-answer": {
    label: "Quick Answer",
    icon: "zap",
    description: "Fast, direct answers. Minimal explanation.",
  },
  tutor: {
    label: "Tutor",
    icon: "graduation-cap",
    description: "Teaches the concept and explains the why, not just the what.",
  },
  "exam-prep": {
    label: "Exam Prep",
    icon: "clipboard-list",
    description: "Structured definitions, key points, and comparisons.",
  },
  research: {
    label: "Research",
    icon: "microscope",
    description: "Deeper, nuanced answers that preserve detail and context.",
  },
};

export const ASSISTANT_MODE_OPTIONS: AssistantMode[] = ["quick-answer", "tutor", "exam-prep", "research"];

export const GROUNDING_INFO: Record<GroundingMode, { label: string; description: string }> = {
  "strict-documents": {
    label: "Strict Documents",
    description: "Answer using only information supported by your documents.",
  },
  "documents-general": {
    label: "Documents + General Knowledge",
    description: "Use your documents first, but use general knowledge when they don't have the answer.",
  },
};

// ---------------------------------------------------------------- validation

const stringEnum =
  <T extends string>(values: readonly T[]) =>
  (value: unknown): value is T =>
    typeof value === "string" && (values as readonly string[]).includes(value);

const isTheme = stringEnum(["system", "light", "dark"] as const);
const isAccent = stringEnum(ACCENT_OPTIONS);
const isFontSize = stringEnum(["small", "medium", "large"] as const);
const isDensity = stringEnum(["compact", "comfortable", "spacious"] as const);
const isMessageStyle = stringEnum(["bubbles", "minimal"] as const);
const isBackground = stringEnum(["solid", "gradient"] as const);
const isResponseStyle = stringEnum(["concise", "balanced", "detailed", "beginner"] as const);
const isResponseFormat = stringEnum(["paragraphs", "bullets", "step-by-step"] as const);
const isSearchDepth = stringEnum(["fast", "balanced", "thorough"] as const);
const isAssistantMode = stringEnum(["quick-answer", "tutor", "exam-prep", "research"] as const);
const isGroundingMode = stringEnum(["strict-documents", "documents-general"] as const);

export function sanitize(raw: unknown): Settings {
  const base: Settings = { ...DEFAULT_SETTINGS };
  if (typeof raw !== "object" || raw === null) return base;
  const r = raw as Record<string, unknown>;

  if (isTheme(r.theme)) base.theme = r.theme;
  if (isAccent(r.accentColor)) base.accentColor = r.accentColor;
  if (isFontSize(r.fontSize)) base.fontSize = r.fontSize;
  if (isDensity(r.density)) base.density = r.density;
  if (isMessageStyle(r.messageStyle)) base.messageStyle = r.messageStyle;
  if (isBackground(r.background)) base.background = r.background;
  if (typeof r.reducedMotion === "boolean") base.reducedMotion = r.reducedMotion;
  if (typeof r.highContrast === "boolean") base.highContrast = r.highContrast;
  if (isResponseStyle(r.responseStyle)) base.responseStyle = r.responseStyle;
  if (isResponseFormat(r.responseFormat)) base.responseFormat = r.responseFormat;
  if (typeof r.showSources === "boolean") base.showSources = r.showSources;
  if (isSearchDepth(r.searchDepth)) base.searchDepth = r.searchDepth;

  // retrievalK: honor a manually tuned value, clamped; depth presets rewrite it
  if (typeof r.retrievalK === "number" && Number.isFinite(r.retrievalK)) {
    base.retrievalK = Math.min(16, Math.max(1, Math.round(r.retrievalK)));
  }

  if (isGroundingMode(r.groundingMode)) base.groundingMode = r.groundingMode;

  if (isAssistantMode(r.assistantMode)) base.assistantMode = r.assistantMode;
  if (typeof r.explainTerms === "boolean") base.explainTerms = r.explainTerms;
  if (typeof r.giveExamples === "boolean") base.giveExamples = r.giveExamples;
  if (typeof r.highlightKeyPoints === "boolean") base.highlightKeyPoints = r.highlightKeyPoints;
  if (typeof r.relatedConcepts === "boolean") base.relatedConcepts = r.relatedConcepts;
  if (typeof r.askClarifyingQuestions === "boolean") base.askClarifyingQuestions = r.askClarifyingQuestions;

  return base;
}

// ---------------------------------------------------------------- persistence

const STORAGE_KEY = "rag-settings";

export function loadSettings(): Settings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return sanitize(JSON.parse(raw));
  } catch {
    // corrupted or malformed storage: fall back to defaults
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: Settings): void {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...settings, version: SETTINGS_VERSION })
    );
  } catch {
    // storage unavailable (private mode/quota): settings stay session-only
  }
}

export function resetSettings(): Settings {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
  return { ...DEFAULT_SETTINGS };
}

// ---------------------------------------------------------------- DOM effects

/** Effective chunks-per-query for the current depth preset. */
export function effectiveK(settings: Settings): number {
  return DEPTH_K[settings.searchDepth] ?? DEFAULT_SETTINGS.retrievalK;
}

export const ACCENT_HEX: Record<AccentColor, string> = {
  blue: "#2563eb",
  purple: "#7c3aed",
  green: "#059669",
  orange: "#ea580c",
  pink: "#db2777",
  red: "#dc2626",
};

const ACCENT_VARS: Record<AccentColor, { accent: string; accentHover: string }> = {
  blue: { accent: "#2563eb", accentHover: "#1d4ed8" },
  purple: { accent: "#7c3aed", accentHover: "#6d28d9" },
  green: { accent: "#059669", accentHover: "#047857" },
  orange: { accent: "#ea580c", accentHover: "#c2410c" },
  pink: { accent: "#db2777", accentHover: "#be185d" },
  red: { accent: "#dc2626", accentHover: "#b91c1c" },
};

const FONT_SIZES: Record<FontSize, string> = {
  small: "15px",
  medium: "16px",
  large: "18px",
};

/**
 * Favicon SVG markup, parameterized by fill color — kept in sync with the
 * static app/icon.svg fallback (same shape) so the tab icon always matches
 * whatever the current accent color is, live, without a page reload.
 */
function faviconSvg(hex: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="${hex}"/><ellipse cx="16" cy="18" rx="11" ry="3.8" fill="none" stroke="#ffffff" stroke-width="1.6" opacity="0.85" transform="rotate(-16 16 18)"/><circle cx="16" cy="14.3" r="6.2" fill="#ffffff" fill-opacity="0.55" stroke="#ffffff" stroke-width="1"/></svg>`;
}

/** Swap the tab favicon to match the given accent color. */
function updateFavicon(hex: string): void {
  const href = `data:image/svg+xml,${encodeURIComponent(faviconSvg(hex))}`;
  let link = document.querySelector<HTMLLinkElement>('link[rel="icon"][data-dynamic-favicon]');
  if (!link) {
    link = document.createElement("link");
    link.rel = "icon";
    link.type = "image/svg+xml";
    link.dataset.dynamicFavicon = "true";
    document.head.appendChild(link);
  }
  link.href = href;
}

/**
 * Apply settings that have a global DOM effect: theme class, accent variables,
 * font size, density, background, motion and contrast classes.
 * Theme "system" is resolved via prefers-color-scheme and kept live via matchMedia.
 */
export function applyAppearance(settings: Settings): () => void {
  if (typeof document === "undefined") return () => {};

  const root = document.documentElement;
  root.classList.remove("theme-light", "theme-dark", "reduce-motion", "high-contrast", "bg-gradient");

  if (settings.theme === "light") root.classList.add("theme-light");
  if (settings.theme === "dark") root.classList.add("theme-dark");

  if (settings.reducedMotion) root.classList.add("reduce-motion");
  if (settings.highContrast) root.classList.add("high-contrast");
  if (settings.background === "gradient") root.classList.add("bg-gradient");

  const accent = ACCENT_VARS[settings.accentColor] ?? ACCENT_VARS.blue;
  root.style.setProperty("--accent", accent.accent);
  root.style.setProperty("--accent-hover", accent.accentHover);
  updateFavicon(accent.accent);

  root.style.setProperty("--base-font-size", FONT_SIZES[settings.fontSize] ?? FONT_SIZES.medium);

  root.dataset.density = settings.density;
  root.dataset.messageStyle = settings.messageStyle;

  // Live-follow the OS theme while on "system"
  if (settings.theme === "system" && typeof window.matchMedia === "function") {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => {
      root.classList.toggle("theme-dark", e.matches);
      root.classList.toggle("theme-light", !e.matches);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }
  return () => {};
}
