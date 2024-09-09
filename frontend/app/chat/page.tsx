'use client';

import { useAuthStore } from '../store';
import PromptContainer from '../components/PromptContainer';

const ChatPage = () => {
  const { user, loading } = useAuthStore();

  if (!user) {
    console.log("User not authenticated, redirecting to login");
    return null;
  }

  return (
    <div className="chat-container">
      {/* <div>Welcome to the Chat, {user.displayName || 'User'}!</div> */}
      <PromptContainer />
    </div>
  );
};

export default ChatPage;