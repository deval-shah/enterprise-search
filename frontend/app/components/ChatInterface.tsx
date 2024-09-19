// app/components/ChatInterface.tsx
import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { FiSend, FiPaperclip} from 'react-icons/fi';
import MessageItem from './MessageItem';
import AnimatedLoadingDots from './AnimatedLoadingDots';
import { toast } from 'react-toastify';
import { Message, ContextDetail, AttachedFile } from '../types';
import { useChatStore, useFileUploadStore } from '../store';
import ContextDetails from './ContextDetails';

const ChatInterface: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { webSocketService } = useAuth();

  // Stores
  const {
    messages, input, isLoading, isWaitingForResponse, metadata, isTyping, fileUploadProgress, fileCount,
    setInput, addMessage, setIsLoading, setIsWaitingForResponse, setMetadata, setIsTyping, updateLastMessage, setFileCount
  } = useChatStore();

  // const { uploadedFiles, setUploadedFiles, clearUploadedFiles } = useFileUploadStore();
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);

  // Limitations
  const maxFileSize = 10;
  const allowedExtensions = ['.pdf', '.txt', '.docx', '.csv'];
  const maxChatFiles = 10;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Handles form submission, sends the query and files to the WebSocket service
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (webSocketService) {
      setIsTyping(true);
      try {
        await webSocketService.sendMessage({
          query: input,
          files: attachedFiles
        });
      } catch (error) {
        console.error('Error occurred:', error);
        addMessage({ role: 'system', content: `Error processing your request. Try again later` });
        setIsTyping(false);
      }
    }
    setFileCount(fileCount + attachedFiles.length);
    setInput('');
    setAttachedFiles([]);
  };
//   useEffect(() => {
//     return () => {
//       clearUploadedFiles();
//     };
//   }, [clearUploadedFiles]);


  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const files = Array.from(event.target.files).map((file) => {
        return Object.assign(file, {
          preview: URL.createObjectURL(file)
        });
      });

      const invalidFileSize = files.filter(file => file.size > maxFileSize * 1024 * 1024);
      const invalidFiles = files.filter(file => {
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();
        return !allowedExtensions.includes(extension);
      });

      if (invalidFiles.length > 0) {
        const invalidFileNames = invalidFiles.map(file => file.name).join(', ');
        alert(`The following files are not allowed: ${invalidFileNames}\nPlease only upload .pdf, .txt, .docx, or .csv files.`);
        return;
      } else if (invalidFileSize.length > 0) {
        const fileNames = invalidFileSize.map(file => `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`).join('\n');
        alert(`The following files exceed the size limit (${maxFileSize} MB):\n${fileNames}`);
        return;
      } else if (fileCount + files.length> maxChatFiles) {
        alert(`You have exceeded the maximum file limit of ${maxChatFiles} files per chat. Please upload no more than ${maxChatFiles} files or start a new chat.`);
        return;
      }

      setAttachedFiles((prevFiles) => [...prevFiles, ...files]);
      // setUploadedFiles(Array.from(event.target.files));
      console.log('Files selected:', Array.from(event.target.files).map(f => ({name: f.name, size: f.size})));
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prevFiles) => {
      const newFiles = [...prevFiles];
      URL.revokeObjectURL(newFiles[index].preview as string);
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  useEffect(() => {
    if (webSocketService) {
      webSocketService.onMessage((data) => {
        switch (data.type) {
          case 'metadata':
            if (typeof data.content === 'object') {
              setMetadata(data.content);
            }
            break;
          case 'chunk':
            setIsTyping(false);
            break;
          case 'end_stream':
            setIsWaitingForResponse(false);
            setIsTyping(false);
            break;
          case 'error':
            if (typeof data.content === 'string') {
              console.error('WebSocket error:', data.content);
              addMessage({ role: 'system', content: `Error: ${data.content}` });
            }
            break;
        }
      });
    }
  }, [webSocketService, setIsWaitingForResponse, setIsTyping, setMetadata, addMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, attachedFiles, scrollToBottom]);

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
        {attachedFiles.length > 0 && (
          <div className="mb-2 max-h-24 overflow-y-auto">
            <h3 className="text-sm font-semibold mb-1">Attached Files:</h3>
            <div className="flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div key={index} className="flex items-center bg-gray-100 rounded-lg px-2 py-1">
                  <span className="text-sm mr-1">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                   X
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
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
              className={`p-2 ${isLoading || !input ? 'text-gray-400' : 'text-blue-500 hover:text-blue-700'}`}
              disabled={isLoading || !input}
            >
              <FiSend className="w-5 h-5" />
            </button>
          </form>
          {/* {uploadedFiles.length > 0 && (
            <div className="mt-2 text-sm text-gray-500">
              {uploadedFiles.length} file(s) selected
            </div>
          )} */}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;