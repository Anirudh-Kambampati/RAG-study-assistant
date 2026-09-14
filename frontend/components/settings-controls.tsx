"use client";

import { useId } from "react";
import { CheckIcon, ModeIcon, type ModeIconName } from "@/components/icons";

// ------------------------------------------------------------- layout pieces

export function SettingsCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="settings-card">
      <header className="settings-card-header">
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </header>
      <div className="settings-card-body">{children}</div>
    </section>
  );
}

export function SettingRow({
  label,
  hint,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="setting-row">
      <div className="setting-label">
        <label htmlFor={htmlFor}>{label}</label>
        {hint && <p className="setting-hint">{hint}</p>}
      </div>
      <div className="setting-control">{children}</div>
    </div>
  );
}

// ------------------------------------------------------------- controls

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: T;
  options: { value: T; label: string; hint?: string }[];
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="segmented" role="radiogroup" aria-label={ariaLabel}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          className={`segmented-option ${value === opt.value ? "selected" : ""}`}
          onClick={() => onChange(opt.value)}
          title={opt.hint}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export function ToggleSwitch({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      className={`toggle-switch ${checked ? "on" : "off"}`}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle-knob" />
    </button>
  );
}

export function Swatches<T extends string>({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: T;
  options: { value: T; label: string; color: string }[];
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="swatches" role="radiogroup" aria-label={ariaLabel}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          aria-label={opt.label}
          title={opt.label}
          className={`swatch ${value === opt.value ? "selected" : ""}`}
          style={{ backgroundColor: opt.color }}
          onClick={() => onChange(opt.value)}
        />
      ))}
    </div>
  );
}

export function ModeGrid<T extends string>({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: T;
  options: { value: T; label: string; icon: ModeIconName; description: string }[];
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="mode-grid" role="radiogroup" aria-label={ariaLabel}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          className={`mode-card ${value === opt.value ? "selected" : ""}`}
          onClick={() => onChange(opt.value)}
        >
          {value === opt.value && (
            <span className="mode-card-check" aria-hidden="true">
              <CheckIcon size={12} />
            </span>
          )}
          <span className="mode-card-icon" aria-hidden="true">
            <ModeIcon name={opt.icon} size={20} />
          </span>
          <span className="mode-card-label">{opt.label}</span>
          <span className="mode-card-desc">{opt.description}</span>
        </button>
      ))}
    </div>
  );
}

export function ChoiceList<T extends string>({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: T;
  options: { value: T; label: string; description: string }[];
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="choice-list" role="radiogroup" aria-label={ariaLabel}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          className={`choice-item ${value === opt.value ? "selected" : ""}`}
          onClick={() => onChange(opt.value)}
        >
          <span className="choice-dot" aria-hidden="true" />
          <span className="choice-text">
            <span className="choice-label">{opt.label}</span>
            <span className="choice-desc">{opt.description}</span>
          </span>
          {value === opt.value && (
            <span className="choice-check" aria-hidden="true">
              <CheckIcon size={14} />
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

export function SettingsSelect<T extends string>({
  id,
  value,
  options,
  onChange,
}: {
  id?: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  const idAttr = useId();
  return (
    <select
      id={id ?? idAttr}
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className="settings-select"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
