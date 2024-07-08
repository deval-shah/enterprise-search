import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  console.log("Middleware triggered for path:", request.nextUrl.pathname);

  const sessionId = request.cookies.get('session_id')?.value;

  // List of paths that should be accessible without authentication
  const publicPaths = ['/login', '/register', '/api/v1/login', '/api/v1/register'];
  
  // Check if the requested path is a public path
  const isPublicPath = publicPaths.some(path => request.nextUrl.pathname.startsWith(path));

  // If it's a public path, allow the request to proceed immediately
  if (isPublicPath) {
    console.log("Public path accessed:", request.nextUrl.pathname);
    return NextResponse.next();
  }

  console.log("Session ID:", sessionId ? "Present" : "Not present");

  // For protected routes, check for authentication
  if (!sessionId) {
    console.log("No session ID found, redirecting to login");
    // Redirect to login if there's no authentication
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  console.log("Session ID found, proceeding to requested path");
  // If there's a session ID, let the request proceed
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
