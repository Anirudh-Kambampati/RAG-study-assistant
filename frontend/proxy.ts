import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// A valid `metis_session` cookie is only ever proof of "logged in as of
// last check" — the middleware can't hit the database from the edge, so it
// only checks presence, not validity. That's fine: this layer exists purely
// to avoid flashing protected UI / redirect loops before the real check
// happens. The backend (auth.get_current_user) is the actual authority and
// 401s every request with a missing/expired/forged session regardless of
// what this middleware decided.
const SESSION_COOKIE = "metis_session";
const PROTECTED_PREFIXES = ["/dashboard", "/chat", "/settings"];
const AUTH_PAGES = ["/login", "/signup"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has(SESSION_COOKIE);

  const isProtected = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
  if (isProtected && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (AUTH_PAGES.includes(pathname) && hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/chat/:path*", "/settings/:path*", "/login", "/signup"],
};
