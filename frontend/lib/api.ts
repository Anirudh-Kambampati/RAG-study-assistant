export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type QuerySource = {
  rank: number;
  score: number | null;
  page: number | null;
  title: string | null;
  snippet: string;
};

export type AssistantMessage = ChatMessage & {
  sources?: QuerySource[];
};

export type ChatEntry = {
  messages: ChatMessage[];
  index_dir: string;
};

export type ChatMap = Record<string, ChatEntry>;

export async function getBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch("/api/chats", { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

async function handleErrors(res: Response): Promise<Response> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return res;
}

export async function fetchChats(): Promise<ChatMap> {
  const res = await handleErrors(await fetch("/api/chats", { cache: "no-store" }));
  return res.json();
}

/** Returns the chat's actual doc_id/slug as the backend created it — the
 * backend sanitizes the requested doc_id (e.g. "Notes (1).pdf" becomes
 * "Notes _1_.pdf"), so callers must navigate using this returned value
 * rather than re-deriving a slug from the original filename themselves. */
export async function createChat(docId: string, file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await handleErrors(
    await fetch(`/api/chats/${encodeURIComponent(docId)}`, {
      method: "POST",
      body: form,
    })
  );
  const body = await res.json();
  return body.doc_id as string;
}

export async function deleteChat(docId: string): Promise<void> {
  const res = await handleErrors(
    await fetch(`/api/chats/${encodeURIComponent(docId)}`, { method: "DELETE" })
  );
  await res.json();
}

export type QueryOptions = {
  /** Chunks to retrieve (1-12, server clamps). */
  k?: number;
  /** Response style preset: concise | balanced | detailed | beginner. */
  style?: string;
  /** Response format: paragraphs | bullets | step-by-step. */
  format?: string;
  /** Assistant mode: quick-answer | tutor | exam-prep | research. */
  assistantMode?: string;
  /** Grounding mode: strict-documents | documents-general. */
  groundingMode?: string;
  explainTerms?: boolean;
  giveExamples?: boolean;
  highlightKeyPoints?: boolean;
  relatedConcepts?: boolean;
  askClarifyingQuestions?: boolean;
};

export async function sendQuery(
  docId: string,
  query: string,
  options: QueryOptions = {}
): Promise<AssistantMessage> {
  const res = await handleErrors(
    await fetch(`/api/chats/${encodeURIComponent(docId)}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        k: options.k ?? null,
        style: options.style ?? null,
        format: options.format ?? null,
        assistant_mode: options.assistantMode ?? null,
        grounding_mode: options.groundingMode ?? null,
        explain_terms: options.explainTerms ?? null,
        give_examples: options.giveExamples ?? null,
        highlight_key_points: options.highlightKeyPoints ?? null,
        related_concepts: options.relatedConcepts ?? null,
        ask_clarifying_questions: options.askClarifyingQuestions ?? null,
      }),
    })
  );
  return res.json();
}
