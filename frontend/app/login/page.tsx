// app/login/page.tsx
'use client';

import { Suspense, lazy } from 'react';
import LoadingSkeleton from './LoadingSkeleton';

const LoginForm = lazy(() => import('./LoginForm'));

export default function Login() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-700">
        <Suspense fallback={<LoadingSkeleton />}>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
