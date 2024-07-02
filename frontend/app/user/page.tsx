'use client';

import { useEffect, useState } from 'react';
import { User } from 'firebase/auth';
import { useRouter } from 'next/navigation';
import { useFirebaseAuth } from '../hooks/useFirebaseAuth';

const UserPage = () => {
  const { user, loading } = useFirebaseAuth();
  const router = useRouter();
  const [cachedUser, setCachedUser] = useState<User | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    } else if (user) {
      // Check if user details are in localStorage
      const storedUser = localStorage.getItem('userDetails');
      if (storedUser) {
        setCachedUser(JSON.parse(storedUser));
      } else {
        // If not in localStorage, set and store
        setCachedUser(user);
        localStorage.setItem('userDetails', JSON.stringify(user));
      }
    }
  }, [user, loading, router]);

  if (loading) return <div>Loading...</div>;
  if (!cachedUser) return null;

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">User Profile</h3>
        </div>
        <div className="border-t border-gray-200">
          <dl>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Full name</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{cachedUser.displayName || 'N/A'}</dd>
            </div>
            <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Email address</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{cachedUser.email}</dd>
            </div>
            <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">User ID</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{cachedUser.uid}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
};

export default UserPage;
