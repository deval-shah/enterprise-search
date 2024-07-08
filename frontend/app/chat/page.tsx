'use client';

import { useAuth } from "../contexts/AuthContext";
import PromptContainer from '../components/PromptContainer';

const ChatPage = () => {
  const { user } = useAuth();

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