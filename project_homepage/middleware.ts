import { clerkMiddleware } from '@clerk/nextjs';

export default clerkMiddleware({
  // Routes that can be accessed while signed out
  publicRoutes: ['/sign-in(.*)', '/sign-up(.*)'],
  // Routes that can always be accessed, and have
  // no authentication information
  ignoredRoutes: ['/api/health'],
});

export const config = {
  // Protects all routes including api/trpc routes
  // Please edit this to allow other routes to be public as needed.
  // See https://clerk.com/docs/references/nextjs/auth-middleware
  // for more information about configuring your Middleware
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
};
