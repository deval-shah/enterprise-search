// PromptContainer.tsx
import React, { useState, Suspense, useEffect } from 'react';
import { useRouter } from "next/navigation";
import dynamic from 'next/dynamic';
import Sidebar from './Sidebar';
import FileUploadDialog from './FileUploadDialog';
import { useAuthStore, useFileUploadStore, useChatStore } from '../store';

// const ChatInterface = dynamic(() => import('./ChatInterface'), {
//   loading: () => <p>Loading chat interface...</p>,
// });

const ChatInterface = dynamic(() => import('./ChatInterface').then(mod => mod.default), {
  loading: () => <p>Loading chat interface...</p>,
  ssr: false
});

const PromptContainer: React.FC = () => {
  const router = useRouter();
  const [showUploadDialog, setShowUploadDialog] = useState(true);
  const { user, loading } = useAuthStore();
  const { uploadedFiles, setUploadedFiles, clearUploadedFiles } = useFileUploadStore();
  const { clearMessages } = useChatStore();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  const handleNewChat = () => {
    setShowUploadDialog(true);
    setUploadedFiles([]);
    clearMessages();
    clearUploadedFiles();
  };

  const handleFileUpload = (files: File[]) => {
    setUploadedFiles(files);
    setShowUploadDialog(false);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen w-full bg-gray-100 dark:bg-gray-900">
      <Sidebar onNewChat={handleNewChat} />
      <div className="flex-1 flex flex-col">
        {showUploadDialog ? (
          <FileUploadDialog onUploadComplete={handleFileUpload} />
        ) : (
          <Suspense fallback={<div>Loading...</div>}>
            <ChatInterface />
          </Suspense>
        )}
      </div>
    </div>
  );
};

export default PromptContainer;
