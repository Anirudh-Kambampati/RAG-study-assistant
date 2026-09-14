"""Prompt composition for the RAG assistant.

The final prompt sent to the LLM is assembled from independent, swappable
sections: base identity, grounding rules, assistant mode, response
style/format, behavior preferences, formatting rules, conversation history,
and retrieved context. Adding a new mode or preference means adding an entry
to one of the dicts below, not touching the assembly logic.
"""

from dataclasses import dataclass

VALID_MODES = {"quick-answer", "tutor", "exam-prep", "research"}
VALID_GROUNDING = {"strict-documents", "documents-general"}
VALID_STYLES = {"concise", "balanced", "detailed", "beginner"}
VALID_FORMATS = {"paragraphs", "bullets", "step-by-step"}

DEFAULT_ASSISTANT_MODE = "tutor"
DEFAULT_GROUNDING_MODE = "strict-documents"


@dataclass(frozen=True)
class AssistantPreferences:
    assistant_mode: str = DEFAULT_ASSISTANT_MODE
    grounding_mode: str = DEFAULT_GROUNDING_MODE
    style: str | None = None
    format: str | None = None
    # Conservative by design: a behavior toggle only activates when the user
    # explicitly enables it, so unset preferences reproduce the pre-existing
    # (untoggled) prompt behavior.
    explain_terms: bool = False
    give_examples: bool = False
    highlight_key_points: bool = False
    related_concepts: bool = False
    ask_clarifying_questions: bool = False


def _bool(value, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def sanitize_preferences(
    assistant_mode: str | None = None,
    grounding_mode: str | None = None,
    style: str | None = None,
    format: str | None = None,
    explain_terms: bool | None = None,
    give_examples: bool | None = None,
    highlight_key_points: bool | None = None,
    related_concepts: bool | None = None,
    ask_clarifying_questions: bool | None = None,
) -> AssistantPreferences:
    """Validate raw, client-provided values into a safe AssistantPreferences.

    Never trust client input directly in the prompt: anything unrecognized
    falls back to the documented default rather than erroring or passing
    through.
    """
    defaults = AssistantPreferences()
    return AssistantPreferences(
        assistant_mode=assistant_mode if assistant_mode in VALID_MODES else defaults.assistant_mode,
        grounding_mode=grounding_mode if grounding_mode in VALID_GROUNDING else defaults.grounding_mode,
        style=style if style in VALID_STYLES else None,
        format=format if format in VALID_FORMATS else None,
        explain_terms=_bool(explain_terms, defaults.explain_terms),
        give_examples=_bool(give_examples, defaults.give_examples),
        highlight_key_points=_bool(highlight_key_points, defaults.highlight_key_points),
        related_concepts=_bool(related_concepts, defaults.related_concepts),
        ask_clarifying_questions=_bool(ask_clarifying_questions, defaults.ask_clarifying_questions),
    )


# --------------------------------------------------------------------------- base

BASE_INSTRUCTIONS = """You are a knowledgeable, patient academic assistant helping a student work through a document they uploaded. Be accurate: never invent facts, quotes, page numbers, or details that are not supported by what you were given."""

FORMATTING_RULES = """Formatting rules:
- Use clear Markdown.
- Use headings (##, ###) to organize longer answers logically.
- Use tables when comparing concepts, differences, or components.
- Use code blocks only for workflows, pipelines, step-by-step technical flows, pseudo-code, or code snippets — never for normal prose.
- Keep formatting clean and purposeful, not decorative for its own sake."""

CITATION_INSTRUCTIONS = """Citations:
- The context below is split into numbered sources: [1], [2], [3], and so on.
- Whenever a sentence or claim draws on one of these sources, cite it inline immediately after that sentence or clause using its bracket number, e.g. "Mitosis produces two identical daughter cells [1]."
- Always use plain ASCII square brackets exactly like this: [1]. Never use full-width brackets (【1】), parentheses, or any other bracket style, and never add a space between the brackets and the number.
- If a claim draws on more than one source, cite them together with no space between, e.g. [1][2].
- Only use citation numbers that actually appear in the numbered context — never invent a number that wasn't given to you, and never cite a source for a claim it doesn't support.
- Do not add a separate "Sources" or "References" section at the end — citations belong inline, next to the claims they support."""


# --------------------------------------------------------------------- grounding
#
# These two instructions are mutually exclusive alternatives, not additive
# layers — "general" fully replaces "strict" rather than loosening it with a
# contradictory append, so the model is never told to use only the context
# and also use outside knowledge in the same breath.

GROUNDING_INSTRUCTIONS: dict[str, str] = {
    "strict-documents": """Grounding: Strict Documents
- Answer using ONLY information supported by the provided context.
- Do not use outside knowledge to fill gaps, and do not guess or assume anything not stated.
- If the context does not contain the answer, say plainly that the document does not cover this. Do not speculate beyond that.""",
    "documents-general": """Grounding: Documents + General Knowledge
- Prioritize the provided context as your primary source. If it fully answers the question, rely on it alone.
- If the context is incomplete or silent on part of the question, you may use general knowledge to fill the gap.
- When you do this, clearly separate the two, e.g. label parts as "From the document" and "From general knowledge".
- Never let general knowledge contradict the context.""",
}


# ------------------------------------------------------------------------- modes

MODE_INSTRUCTIONS: dict[str, str] = {
    "quick-answer": """Mode: Quick Answer
- Lead with the direct answer in the first sentence or two, before any explanation.
- Keep the whole response short — a few sentences or one tight paragraph.
- Avoid background, caveats, or extended reasoning unless the user explicitly asks for it.
- Do not restate the question or add a closing summary.""",
    "tutor": """Mode: Tutor
- Teach the concept rather than only stating the answer — help the user understand *why*, not just *what*.
- Break difficult ideas into smaller pieces and build up to the full answer.
- Use a calm, encouraging, slightly conversational tone.
- Show the reasoning steps, not just the conclusion.""",
    "exam-prep": """Mode: Exam Prep
- Optimize for exam usefulness: definitions, key facts, formulas, steps, and comparisons.
- Prefer structured output — headings, bullet points, or tables — over long prose.
- When the context supports it, call out points that are commonly tested (key distinctions, formulas, commonly confused terms).
- Skip conversational filler and do not restate the question.""",
    "research": """Mode: Research
- Give a deeper, well-structured answer that preserves nuance rather than oversimplifying.
- Clearly distinguish claims that come from the retrieved context from anything else you add.
- When the context includes multiple relevant points, compare or contrast them rather than flattening them into one statement.
- It is fine for this answer to be longer than usual when the depth is warranted.""",
}


# --------------------------------------------------------------------- behavior

def build_behavior_instructions(prefs: AssistantPreferences) -> str:
    lines: list[str] = []

    if prefs.explain_terms:
        lines.append(
            "- When specialized or technical terms appear, briefly explain them, at a depth that fits the current mode."
        )
    if prefs.give_examples:
        lines.append(
            "- Include an example where it would help clarify a concept. If an example is not drawn from the document, "
            "make clear it is an illustrative example rather than something the document itself states."
        )
    if prefs.highlight_key_points:
        lines.append(
            "- Make the most important information visually obvious using bold text, bullets, or headings as appropriate."
        )
    if prefs.related_concepts:
        lines.append(
            "- Where genuinely relevant, briefly mention closely related concepts that add useful context. Do not wander into unrelated territory."
        )
    if prefs.ask_clarifying_questions:
        lines.append(
            "- If the question is genuinely ambiguous or missing information needed to answer well, ask a clarifying "
            "question instead of guessing. Only do this when the ambiguity is real — do not ask when the answer is "
            "already clear from the context and question."
        )

    if not lines:
        return ""
    return "Response behavior:\n" + "\n".join(lines)


# ----------------------------------------------------------------- style/format

def build_style_instructions(style: str | None, fmt: str | None) -> str:
    """Translate the pre-existing response style/format preferences into instructions."""
    instructions: list[str] = []

    if style == "concise":
        instructions.append("Keep the answer short and to the point. Skip lengthy explanations.")
    elif style == "detailed":
        instructions.append("Give a thorough, in-depth explanation with examples and detail.")
    elif style == "beginner":
        instructions.append(
            "Explain everything from scratch as if the reader is new to the topic. Avoid jargon, or briefly define any technical term you use."
        )

    if fmt == "bullets":
        instructions.append("Structure the answer as bullet points, with a one-line summary at the end.")
    elif fmt == "step-by-step":
        instructions.append("Structure the answer as numbered, sequential steps.")

    if not instructions:
        return ""
    return "User preferences:\n" + "\n".join(f"- {line}" for line in instructions)


# ----------------------------------------------------------------------- history

def build_history_text(messages: list[dict], max_messages: int = 10, max_chars: int = 400) -> str:
    """Render the last few messages as plain text for light conversational continuity.

    Kept short and separate from `context` so the model can't confuse prior
    chat content with retrieved document content.
    """
    if not messages:
        return ""
    recent = messages[-max_messages:]
    lines = []
    for m in recent:
        role = "Student" if m.get("role") == "user" else "Assistant"
        content = str(m.get("content", ""))[:max_chars]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


# --------------------------------------------------------------------- assembly

def assemble_prompt(prefs: AssistantPreferences, context: str, history: str, query: str) -> str:
    sections = [
        BASE_INSTRUCTIONS,
        GROUNDING_INSTRUCTIONS[prefs.grounding_mode],
        MODE_INSTRUCTIONS[prefs.assistant_mode],
        FORMATTING_RULES,
        CITATION_INSTRUCTIONS,
    ]

    behavior = build_behavior_instructions(prefs)
    if behavior:
        sections.append(behavior)

    style = build_style_instructions(prefs.style, prefs.format)
    if style:
        sections.append(style)

    if history:
        sections.append("Recent conversation (for context only — answer the new question below):\n" + history)

    sections.append(f"Context:\n{context}")
    sections.append(f"Question:\n{query}")
    sections.append("Answer:")

    return "\n\n".join(sections)
