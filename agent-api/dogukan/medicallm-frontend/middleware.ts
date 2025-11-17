import { auth } from "@/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const { pathname } = req.nextUrl;
  
  // Allow access to auth pages (signin, signup)
  if (pathname.startsWith("/auth/")) {
    return NextResponse.next();
  }
  
  // If user is not authenticated and trying to access protected route
  if (!req.auth && pathname !== "/auth/signin" && pathname !== "/auth/signup") {
    const signInUrl = new URL("/auth/signin", req.url);
    return NextResponse.redirect(signInUrl);
  }
  
  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};

