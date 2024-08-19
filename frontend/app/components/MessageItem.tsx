// app/components/MessageItem.tsx
import React, { useState, useEffect } from 'react';
import { FiThumbsUp, FiThumbsDown, FiCopy, FiUser } from 'react-icons/fi';
import ContextDetails from './ContextDetails';
import { Message } from '../types';

const MessageItem: React.FC<{ message: Message }> = ({ message }) => {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [copied, setCopied] = useState(false);
  const [displayContent, setDisplayContent] = useState(message.content);

  const handleFeedback = (type: 'like' | 'dislike') => {
    setFeedback(type);
    console.log(`Feedback for message: ${type}`);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    setDisplayContent(message.content);
  }, [message.content]);

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg p-3 ${
        message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'
      }`}>
        <p>{displayContent}</p>
        {message.role === 'assistant' && (
          <>
            <div className="flex items-center mt-2 space-x-2">
              <button onClick={() => handleFeedback('like')} className={`text-sm ${feedback === 'like' ? 'text-green-500' : 'text-gray-500'}`}>
                <FiThumbsUp />
              </button>
              <button onClick={() => handleFeedback('dislike')} className={`text-sm ${feedback === 'dislike' ? 'text-red-500' : 'text-gray-500'}`}>
                <FiThumbsDown />
              </button>
              <button onClick={handleCopy} className={`text-sm ${copied ? 'text-green-500' : 'text-gray-500'}`}>
                <FiCopy />
              </button>
              {copied && <span className="text-xs text-green-500">Copied!</span>}
            </div>
            {message.context && <ContextDetails context={message.context} />}
          </>
        )}
      </div>
    </div>
  );
}

export default MessageItem;
