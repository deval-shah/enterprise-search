// app/components/ChatInterface.tsx
import React, {  useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { FiSend, FiPaperclip } from 'react-icons/fi';
import MessageItem from './MessageItem';
import AnimatedLoadingDots from './AnimatedLoadingDots';
import { toast } from 'react-toastify';
import { Message, ContextDetail } from '../types';
import { useChatStore, useFileUploadStore } from '../store';
import ContextDetails from './ContextDetails';

const ChatInterface: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { webSocketService } = useAuth();

  // Stores
  const {
    messages, input, isLoading, isWaitingForResponse, metadata, isTyping, fileUploadProgress,
    setInput, addMessage, setIsLoading, setIsWaitingForResponse, setMetadata, setIsTyping, updateFileUploadProgress
  } = useChatStore();

  const { uploadedFiles, setUploadedFiles, clearUploadedFiles } = useFileUploadStore();

   const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Handles form submission, sends the query and files to the WebSocket service
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (webSocketService) {
      setIsTyping(true);
      await webSocketService.sendMessage({ 
        query: input, 
        files: uploadedFiles.map(file => ({ name: file.name, file }))
      });
    }
    setInput('');
    clearUploadedFiles();
  };

  useEffect(() => {
    return () => {
      clearUploadedFiles();
    };
  }, [clearUploadedFiles]);

  
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setUploadedFiles(Array.from(event.target.files));
      console.log('Files selected:', Array.from(event.target.files).map(f => ({name: f.name, size: f.size})));
    }
  };

  useEffect(() => {
    if (webSocketService) {
      webSocketService.onMessage((data) => {
        switch (data.type) {
          case 'chunk':
            setIsTyping(false);
            break;
          case 'metadata':
            setMetadata(data);
            break;
          case 'end_stream':
            setIsWaitingForResponse(false);
            setIsTyping(false);
            break;
        }
      });
    }
  }, [webSocketService, setIsWaitingForResponse, setIsTyping, setMetadata]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-800">
          <div className="flex-1 overflow-y-auto p-4">
              <div className="max-w-2xl mx-auto">
                  {messages.map((message, index) => (
                    <MessageItem key={index} message={message} />
                  ))}
                  {isTyping && (
                    <div className="flex justify-start my-2">
                      <div className="bg-gray-200 rounded-lg p-2">
                        <AnimatedLoadingDots />
                      </div>
                    </div>
                  )}
                  {metadata && <ContextDetails context={metadata.context} />}
                  
                  {/* {Object.entries(fileUploadProgress).map(([filename, progress]) => (
                    <div key={filename} className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 my-2">
                      <div className="bg-blue-600 h-2.5 rounded-full" style={{width: `${progress}%`}}></div>
                    </div>
                  ))} */}
                  <div ref={messagesEndRef} />
              </div>
          </div>
          <div className="p-4">
              <div className="max-w-2xl mx-auto">
              <form onSubmit={handleSubmit} className="flex items-center space-x-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  className="hidden"
                  multiple
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-500 hover:text-gray-700"
                  disabled={isLoading}
                >
                  <FiPaperclip className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-1 p-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Type your message..."
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  className="p-2 text-blue-500 hover:text-blue-700"
                  disabled={isLoading}
                >
                  <FiSend className="w-5 h-5" />
                </button>
              </form>
              {uploadedFiles.length > 0 && (
                  <div className="mt-2 text-sm text-gray-500">
                      {uploadedFiles.length} file(s) selected
                  </div>
              )}
              </div>
          </div>
      </div>
  );
};

export default ChatInterface;