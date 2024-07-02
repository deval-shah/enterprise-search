// import { NextRequest, NextResponse } from "next/server";
// import { authMiddleware, redirectToHome, redirectToLogin } from "next-firebase-auth-edge";
// import { clientConfig, serverConfig } from "./config";

// const PUBLIC_PATHS = ['/register', '/login'];
// const TOKEN_REFRESH_THRESHOLD = 5 * 60;

// export async function middleware(request: NextRequest) {
//   return authMiddleware(request, {
//     loginPath: "/api/login",
//     logoutPath: "/api/logout",
//     apiKey: clientConfig.apiKey,
//     cookieName: serverConfig.cookieName,
//     cookieSignatureKeys: serverConfig.cookieSignatureKeys,
//     cookieSerializeOptions: serverConfig.cookieSerializeOptions,
//     serviceAccount: serverConfig.serviceAccount,
//     handleValidToken: async ({ token, decodedToken }, headers) => {
//       if (PUBLIC_PATHS.includes(request.nextUrl.pathname)) {
//         return redirectToHome(request);
//       }

//       // // Check if token needs refresh
//       // const now = Math.floor(Date.now() / 1000);
//       // if (decodedToken.exp - now < TOKEN_REFRESH_THRESHOLD) {
//       //   // Implement token refresh logic here
//       //   console.log('Token needs refresh');
//       //   // You might want to call a refresh token API here
//       // }

//       return NextResponse.next({
//         request: {
//           headers
//         }
//       });
//     },
//     handleInvalidToken: async (reason) => {
//       console.info('Missing or malformed credentials', { reason });

//       return redirectToLogin(request, {
//         path: '/login',
//         publicPaths: PUBLIC_PATHS
//       });
//     },
//     handleError: async (e: unknown) => {
//       const error = e as { status: number };
//       console.error('Authentication error:', error);

//       if (error.status === 401) {
//         console.log('Unauthorized access attempt');
//       } else if (error.status === 403) {
//         console.log('Forbidden access attempt');
//       }

//       return redirectToLogin(request, {
//         path: '/login',
//         publicPaths: PUBLIC_PATHS
//       });
//     }
//   });
// }

// // export async function middleware(request: NextRequest) {
// //   // return authMiddleware(request, {
// //   //   // ...
// //   // });
// //   return NextResponse.next();
// // }

// export const config = {
//   matcher: [
//     "/",
//     "/((?!_next|api|.*\\.).*)",
//     "/api/login",
//     "/api/logout"
//   ],
// };

// middleware.ts

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
