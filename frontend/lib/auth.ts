export type User = {
  id: string;
  name: string;
  email: string;
};

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (Array.isArray(body?.detail)) {
      // FastAPI/Pydantic validation error shape
      return body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ") || "Invalid input";
    }
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // ignore non-JSON error bodies
  }
  return res.statusText || "Request failed";
}

export async function getCurrentUser(): Promise<User | null> {
  const res = await fetch("/api/auth/me", { cache: "no-store" });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function signup(name: string, email: string, password: string): Promise<User> {
  const res = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function login(email: string, password: string): Promise<User> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
}
