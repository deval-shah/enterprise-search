// app/components/ChatInterface.tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { FiSend, FiPaperclip } from 'react-icons/fi';
import MessageItem from './MessageItem';
import { Message, ContextDetail } from '../types';
import AnimatedLoadingDots from './AnimatedLoadingDots';

interface ChatInterfaceProps {
  initialFiles: File[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ initialFiles }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>(initialFiles);
  const { getAuthHeader } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);

  const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
      scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && uploadedFiles.length === 0) return;

    const newMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, newMessage]);
    setInput('');
    setIsLoading(true);
    setIsWaitingForResponse(true);

    try {
      const headers = await getAuthHeader();
      delete (headers as Record<string, string>)['Content-Type'];
      const formData = new FormData();
      formData.append('query', input);
      uploadedFiles.forEach(file => formData.append('files', file));

      const response = await fetch('/api/actions/handleMessage', {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: Message = { 
        role: 'assistant', 
        content: data.response,
        context: data.context as ContextDetail[]
      };
      setIsWaitingForResponse(false);
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = { role: 'system', content: 'Sorry, an error occurred. Please try again.' };
      setIsWaitingForResponse(false);
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setUploadedFiles([]);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.files) {
          const newFiles = Array.from(event.target.files);
          setUploadedFiles(prevFiles => [...prevFiles, ...newFiles]);
      }
  };

  const loadingMessage: Message = { role: 'system', content: '...' };
  return (
      <div className="flex flex-col h-full bg-white">
          <div className="flex-1 overflow-y-auto p-4">
              <div className="max-w-2xl mx-auto">
                  {messages.map((message, index) => (
                    <MessageItem key={index} message={message} />
                  ))}
                  {isWaitingForResponse && (
                    <div className="flex justify-center my-4">
                      <div className="rounded-full px-4 py-2">
                        <AnimatedLoadingDots />
                      </div>
                    </div>
                  )}
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
                          className="flex-1 p-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
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