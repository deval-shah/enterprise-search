// app/login/page.tsx
'use client';

import { Suspense, lazy, useEffect } from 'react';
import LoadingSkeleton from './LoadingSkeleton';
import { useAuthStore } from '../store';
import { useRouter } from 'next/navigation';

const LoginForm = lazy(() => import('./LoginForm'));

export default function Login() {
  const { user, loading } = useAuthStore();
  const router = useRouter();

  // if (loading) {
  //   return <LoadingSkeleton />;
  // }

  // if (user && !loading) {
  //   router.push('/chat');
  //   return null;
  // }

//   useEffect(() => {
//     if (user && !loading) {
//       router.replace('/chat');
//     }
//   }, [user, loading, router]);

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
