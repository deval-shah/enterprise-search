// PromptContainer.tsx
import React, { useState, Suspense, useEffect } from 'react';
import { useRouter } from "next/navigation";
import dynamic from 'next/dynamic';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from './Sidebar';
import FileUploadDialog from './FileUploadDialog';

const ChatInterface = dynamic(() => import('./ChatInterface'), {
  loading: () => <p>Loading chat interface...</p>,
});

const PromptContainer: React.FC = () => {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [showUploadDialog, setShowUploadDialog] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  const handleNewChat = () => {
    setShowUploadDialog(true);
    setUploadedFiles([]);
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
            <ChatInterface initialFiles={uploadedFiles} />
          </Suspense>
        )}
      </div>
    </div>
  );
};

export default PromptContainer;
