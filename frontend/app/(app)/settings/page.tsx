"use client";

import { useState } from "react";
import { useSettings } from "@/components/SettingsProvider";
import {
  SettingsCard,
  SettingRow,
  SegmentedControl,
  ToggleSwitch,
  Swatches,
  ModeGrid,
  ChoiceList,
} from "@/components/settings-controls";
import {
  ACCENT_HEX,
  ACCENT_OPTIONS,
  ASSISTANT_MODE_INFO,
  ASSISTANT_MODE_OPTIONS,
  DEPTH_INFO,
  GROUNDING_INFO,
  type AccentColor,
  type AssistantMode,
  type Density,
  type FontSize,
  type GroundingMode,
  type MessageStyle,
  type ResponseFormat,
  type ResponseStyle,
  type SearchDepth,
  type ThemeSetting,
} from "@/lib/settings";

const SECTIONS = [
  { id: "general", label: "General" },
  { id: "chat", label: "Chat" },
  { id: "knowledge", label: "Knowledge" },
  { id: "assistant", label: "Assistant" },
  { id: "appearance", label: "Appearance" },
  { id: "accessibility", label: "Accessibility" },
  { id: "privacy", label: "Privacy & Data" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

const ACCENT_SWATCHES = ACCENT_OPTIONS.map((c) => ({
  value: c,
  label: c[0].toUpperCase() + c.slice(1),
  color: ACCENT_HEX[c],
}));

export default function SettingsPage() {
  const { settings, update, reset } = useSettings();
  const [active, setActive] = useState<SectionId>("general");

  // Privacy & data action state
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<{ ok: boolean; message: string } | null>(null);

  function currentChatId(): string | null {
    if (typeof window === "undefined") return null;
    const m = window.location.pathname.match(/^\/chat\/(.+)$/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  async function runAction(key: string, fn: () => Promise<string>) {
    setBusyAction(key);
    setActionResult(null);
    try {
      setActionResult({ ok: true, message: await fn() });
    } catch (err) {
      setActionResult({
        ok: false,
        message: err instanceof Error ? err.message : "Request failed",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function clearConversation() {
    const docId = currentChatId();
    if (!docId) {
      setActionResult({ ok: false, message: "No chat is currently open." });
      return;
    }
    if (!confirm(`Clear all messages in "${docId}"? The indexed document is kept.`)) return;
    await runAction("clear", async () => {
      const res = await fetch(`/api/chats/${encodeURIComponent(docId)}/clear`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? res.statusText);
      }
      return `Cleared conversation "${docId}".`;
    });
  }

  async function clearAllConversations() {
    if (!confirm("Delete ALL conversations? Indexed documents are kept.")) return;
    if (!confirm("This cannot be undone. Continue?")) return;
    await runAction("clearAll", async () => {
      const res = await fetch("/api/chats", { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? res.statusText);
      }
      return "All conversations deleted.";
    });
  }

  async function exportConversation() {
    const docId = currentChatId();
    if (!docId) {
      setActionResult({ ok: false, message: "No chat is currently open." });
      return;
    }
    await runAction("export", async () => {
      const res = await fetch(`/api/chats/${encodeURIComponent(docId)}/export`);
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? res.statusText);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${docId}.md`;
      a.click();
      URL.revokeObjectURL(url);
      return `Exported "${docId}" as Markdown.`;
    });
  }

  const chatOpen = currentChatId() !== null;

  return (
    <main className="settings-page">
      <header className="settings-header">
        <h1>Settings</h1>
        <p className="muted">Preferences are saved on this device.</p>
      </header>

      <div className="settings-layout">
        <nav aria-label="Settings sections" className="settings-nav">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              className={`settings-nav-item ${active === s.id ? "active" : ""}`}
              aria-current={active === s.id ? "page" : undefined}
              onClick={() => setActive(s.id)}
            >
              {s.label}
            </button>
          ))}
        </nav>

        <div className="settings-content">
          {actionResult && (
            <div className={`settings-banner ${actionResult.ok ? "ok" : "err"}`} role="status">
              {actionResult.message}
            </div>
          )}

          {active === "general" && (
            <>
              <SettingsCard
                title="General"
                description="Basic preferences for the whole application."
              >
                <SettingRow
                  label="Sources panel"
                  hint="Show the “Sources” list under assistant answers."
                >
                  <ToggleSwitch
                    checked={settings.showSources}
                    onChange={(v) => update({ showSources: v })}
                    label="Show sources panel"
                  />
                </SettingRow>
                <SettingRow
                  label="Reset preferences"
                  hint="Restore all settings to their defaults on this device."
                >
                  <button className="btn-secondary" onClick={reset}>
                    Reset to defaults
                  </button>
                </SettingRow>
              </SettingsCard>
            </>
          )}

          {active === "chat" && (
            <SettingsCard
              title="Chat"
              description="How the assistant writes its answers. Applies to your next question."
            >
              <SettingRow
                label="Response style"
                hint="Concise keeps it short; Detailed is thorough; Beginner-friendly explains from scratch."
              >
                <SegmentedControl<ResponseStyle>
                  value={settings.responseStyle}
                  onChange={(v) => update({ responseStyle: v })}
                  ariaLabel="Response style"
                  options={[
                    { value: "concise", label: "Concise" },
                    { value: "balanced", label: "Balanced" },
                    { value: "detailed", label: "Detailed" },
                    { value: "beginner", label: "Beginner-friendly" },
                  ]}
                />
              </SettingRow>
              <SettingRow label="Response format" hint="How the answer is structured.">
                <SegmentedControl<ResponseFormat>
                  value={settings.responseFormat}
                  onChange={(v) => update({ responseFormat: v })}
                  ariaLabel="Response format"
                  options={[
                    { value: "paragraphs", label: "Paragraphs" },
                    { value: "bullets", label: "Bullet points" },
                    { value: "step-by-step", label: "Step-by-step" },
                  ]}
                />
              </SettingRow>
              <SettingRow label="Sources" hint="Show the “Sources” list under assistant answers.">
                <ToggleSwitch
                  checked={settings.showSources}
                  onChange={(v) => update({ showSources: v })}
                  label="Show sources"
                />
              </SettingRow>
            </SettingsCard>
          )}

          {active === "knowledge" && (
            <>
              <SettingsCard
                title="Knowledge"
                description="How the assistant searches your document before answering."
              >
                <SettingRow
                  label="Search depth"
                  hint={DEPTH_INFO[settings.searchDepth].description}
                >
                  <SegmentedControl<SearchDepth>
                    value={settings.searchDepth}
                    onChange={(v) => update({ searchDepth: v })}
                    ariaLabel="Search depth"
                    options={(Object.keys(DEPTH_INFO) as SearchDepth[]).map((d) => ({
                      value: d,
                      label: DEPTH_INFO[d].label,
                      hint: DEPTH_INFO[d].description,
                    }))}
                  />
                </SettingRow>
                <SettingRow
                  label="Search scope"
                  hint="Searches the document of the chat you are in. Searching across all documents is planned for a future update."
                >
                  <span className="badge-muted">Current document</span>
                </SettingRow>
              </SettingsCard>

              <SettingsCard
                title="Grounding"
                description="How much the assistant is allowed to rely on knowledge outside your document."
              >
                <ChoiceList<GroundingMode>
                  value={settings.groundingMode}
                  onChange={(v) => update({ groundingMode: v })}
                  ariaLabel="Grounding"
                  options={(Object.keys(GROUNDING_INFO) as GroundingMode[]).map((g) => ({
                    value: g,
                    label: GROUNDING_INFO[g].label,
                    description: GROUNDING_INFO[g].description,
                  }))}
                />
              </SettingsCard>
            </>
          )}

          {active === "assistant" && (
            <>
              <SettingsCard
                title="Assistant mode"
                description="Changes how the assistant explains things — teaching style, depth, and structure. Applies to your next question."
              >
                <ModeGrid<AssistantMode>
                  value={settings.assistantMode}
                  onChange={(v) => update({ assistantMode: v })}
                  ariaLabel="Assistant mode"
                  options={ASSISTANT_MODE_OPTIONS.map((m) => ({
                    value: m,
                    label: ASSISTANT_MODE_INFO[m].label,
                    icon: ASSISTANT_MODE_INFO[m].icon,
                    description: ASSISTANT_MODE_INFO[m].description,
                  }))}
                />
              </SettingsCard>

              <SettingsCard
                title="Response behavior"
                description="Fine-tune how answers are explained, independent of the mode above."
              >
                <SettingRow
                  label="Explain difficult terms"
                  hint="Briefly define specialized or technical terms when they appear."
                >
                  <ToggleSwitch
                    checked={settings.explainTerms}
                    onChange={(v) => update({ explainTerms: v })}
                    label="Explain difficult terms"
                  />
                </SettingRow>
                <SettingRow
                  label="Give examples"
                  hint="Add an example when it helps clarify a concept."
                >
                  <ToggleSwitch
                    checked={settings.giveExamples}
                    onChange={(v) => update({ giveExamples: v })}
                    label="Give examples"
                  />
                </SettingRow>
                <SettingRow
                  label="Highlight key points"
                  hint="Make important information visually obvious with bullets, bold, or headings."
                >
                  <ToggleSwitch
                    checked={settings.highlightKeyPoints}
                    onChange={(v) => update({ highlightKeyPoints: v })}
                    label="Highlight key points"
                  />
                </SettingRow>
                <SettingRow
                  label="Include related concepts"
                  hint="Mention closely related concepts when genuinely useful."
                >
                  <ToggleSwitch
                    checked={settings.relatedConcepts}
                    onChange={(v) => update({ relatedConcepts: v })}
                    label="Include related concepts"
                  />
                </SettingRow>
                <SettingRow
                  label="Ask clarifying questions"
                  hint="Ask instead of guessing when a question is genuinely ambiguous."
                >
                  <ToggleSwitch
                    checked={settings.askClarifyingQuestions}
                    onChange={(v) => update({ askClarifyingQuestions: v })}
                    label="Ask clarifying questions"
                  />
                </SettingRow>
              </SettingsCard>
            </>
          )}

          {active === "appearance" && (
            <>
              <SettingsCard title="Theme" description="Make the app feel like yours.">
                <SettingRow label="Theme" hint="Follow the system setting or force light/dark.">
                  <SegmentedControl<ThemeSetting>
                    value={settings.theme}
                    onChange={(v) => update({ theme: v })}
                    ariaLabel="Theme"
                    options={[
                      { value: "system", label: "System" },
                      { value: "light", label: "Light" },
                      { value: "dark", label: "Dark" },
                    ]}
                  />
                </SettingRow>
                <SettingRow label="Accent color" hint="Used for links, highlights and your messages.">
                  <Swatches
                    value={settings.accentColor}
                    onChange={(v: AccentColor) => update({ accentColor: v })}
                    ariaLabel="Accent color"
                    options={ACCENT_SWATCHES}
                  />
                </SettingRow>
                <SettingRow label="Background" hint="Solid or a subtle gradient behind the chat.">
                  <SegmentedControl<"solid" | "gradient">
                    value={settings.background}
                    onChange={(v) => update({ background: v })}
                    ariaLabel="Background"
                    options={[
                      { value: "solid", label: "Solid" },
                      { value: "gradient", label: "Subtle gradient" },
                    ]}
                  />
                </SettingRow>
              </SettingsCard>

              <SettingsCard title="Messages" description="How the conversation looks.">
                <SettingRow label="Message style" hint="Bubbles frame each message; minimal keeps it flat.">
                  <SegmentedControl<MessageStyle>
                    value={settings.messageStyle}
                    onChange={(v) => update({ messageStyle: v })}
                    ariaLabel="Message style"
                    options={[
                      { value: "bubbles", label: "Bubbles" },
                      { value: "minimal", label: "Minimal" }
                    ]}
                  />
                </SettingRow>
                <SettingRow label="Chat density" hint="How much breathing room messages get.">
                  <SegmentedControl<Density>
                    value={settings.density}
                    onChange={(v) => update({ density: v })}
                    ariaLabel="Chat density"
                    options={[
                      { value: "compact", label: "Compact" },
                      { value: "comfortable", label: "Comfortable" },
                      { value: "spacious", label: "Spacious" },
                    ]}
                  />
                </SettingRow>
                <SettingRow label="Font size" hint="Interface text size across the app.">
                  <SegmentedControl<FontSize>
                    value={settings.fontSize}
                    onChange={(v) => update({ fontSize: v })}
                    ariaLabel="Font size"
                    options={[
                      { value: "small", label: "Small" },
                      { value: "medium", label: "Medium" },
                      { value: "large", label: "Large" },
                    ]}
                  />
                </SettingRow>
              </SettingsCard>

              <SettingsCard title="Preview" description="Live preview of your choices.">
                <div
                  className="settings-preview"
                  data-message-style={settings.messageStyle}
                  data-density={settings.density}
                >
                  <div className="preview-bubble preview-user">What is photosynthesis?</div>
                  <div className="preview-bubble preview-assistant">
                    Plants capture sunlight and convert it into chemical energy stored as glucose.
                  </div>
                  <div className="preview-actions">
                    <button className="preview-btn">Accent button</button>
                    <span className="preview-link">Link style</span>
                  </div>
                </div>
              </SettingsCard>
            </>
          )}

          {active === "accessibility" && (
            <SettingsCard
              title="Accessibility"
              description="Comfort options. Reduced motion also follows your OS setting automatically."
            >
              <SettingRow
                label="High contrast"
                hint="Stronger borders and text for better readability."
              >
                <ToggleSwitch
                  checked={settings.highContrast}
                  onChange={(v) => update({ highContrast: v })}
                  label="High contrast"
                />
              </SettingRow>
              <SettingRow
                label="Reduce motion"
                hint="Turns off animations and smooth scrolling."
              >
                <ToggleSwitch
                  checked={settings.reducedMotion}
                  onChange={(v) => update({ reducedMotion: v })}
                  label="Reduce motion"
                />
              </SettingRow>
              <SettingRow
                label="Larger text"
                hint="Quickly switch the interface to the larger font size."
              >
                <ToggleSwitch
                  checked={settings.fontSize === "large"}
                  onChange={(v) => update({ fontSize: v ? "large" : "medium" })}
                  label="Larger text"
                />
              </SettingRow>
            </SettingsCard>
          )}

          {active === "privacy" && (
            <>
              <SettingsCard
                title="Your data"
                description="Conversations live on this machine; preferences live in this browser. Nothing is sent anywhere else."
              >
                <SettingRow
                  label="Export current conversation"
                  hint="Downloads the open chat as a Markdown file."
                >
                  <button
                    className="btn-secondary"
                    onClick={exportConversation}
                    disabled={busyAction !== null}
                  >
                    {busyAction === "export" ? "Working…" : "Export as Markdown"}
                  </button>
                </SettingRow>
                <SettingRow
                  label="Clear current conversation"
                  hint="Removes messages of the chat you have open; keeps the indexed document."
                >
                  <button
                    className="btn-secondary"
                    onClick={clearConversation}
                    disabled={busyAction !== null}
                  >
                    {busyAction === "clear" ? "Working…" : "Clear conversation"}
                  </button>
                </SettingRow>
              </SettingsCard>

              <SettingsCard
                title="Danger zone"
                description="These actions cannot be undone."
              >
                <SettingRow
                  label="Clear all conversations"
                  hint="Deletes every conversation, on this server, but keeps indexed documents."
                >
                  <button
                    className="btn-danger"
                    onClick={clearAllConversations}
                    disabled={busyAction !== null}
                  >
                    {busyAction === "clearAll" ? "Working…" : "Clear all conversations"}
                  </button>
                </SettingRow>
              </SettingsCard>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
