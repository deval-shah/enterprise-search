'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { useAuthStore, useChatHistoryStore, useUiStore } from '../store';
import { ChevronLeft, ChevronRight, Plus, User, Settings, LogOut } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onNewChat }) => {
  const router = useRouter();
  const { logout } = useAuth();
  // Stores
  const { user } = useAuthStore();
  const { chats } = useChatHistoryStore();
  const { isSidebarCollapsed, activeChat, setIsSidebarCollapsed, setActiveChat } = useUiStore();

  const handleLogout = async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Failed to log out', error);
    }
  };

  if (!user) return null;

  return (
    <aside className={`relative flex h-screen transition-all duration-300 ease-in-out ${
      isSidebarCollapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="flex h-full w-full flex-col overflow-hidden bg-slate-50 pt-8 dark:bg-slate-900">
        <div className="flex items-center px-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 text-blue-600" fill="currentColor" strokeWidth="1" viewBox="0 0 24 24">
            <path d="M20.553 3.105l-6 3C11.225 7.77 9.274 9.953 8.755 12.6c-.738 3.751 1.992 7.958 2.861 8.321A.985.985 0 0012 21c6.682 0 11-3.532 11-9 0-6.691-.9-8.318-1.293-8.707a1 1 0 00-1.154-.188zm-7.6 15.86a8.594 8.594 0 015.44-8.046 1 1 0 10-.788-1.838 10.363 10.363 0 00-6.393 7.667 6.59 6.59 0 01-.494-3.777c.4-2 1.989-3.706 4.728-5.076l5.03-2.515A29.2 29.2 0 0121 12c0 4.063-3.06 6.67-8.046 6.965zM3.523 5.38A29.2 29.2 0 003 12a6.386 6.386 0 004.366 6.212 1 1 0 11-.732 1.861A8.377 8.377 0 011 12c0-6.691.9-8.318 1.293-8.707a1 1 0 011.154-.188l6 3A1 1 0 018.553 7.9z"></path>
          </svg>
          {!isSidebarCollapsed && (
            <h2 className="px-5 text-lg font-medium text-slate-800 dark:text-slate-200">
              Chats
            </h2>
          )}
        </div>
        <div className="mt-8 px-2">
          <button 
            onClick={onNewChat}
            className={`flex w-full items-center gap-x-4 rounded-lg border border-slate-300 p-2 text-left text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 focus:outline-none dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800 ${
              isSidebarCollapsed ? 'justify-center' : ''
            }`}
          >
            <Plus size={20} />
            {!isSidebarCollapsed && <span>New Chat</span>}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto border-b border-slate-300 px-2 py-4 dark:border-slate-700">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => setActiveChat(chat.id)}
              className={`w-full truncate text-left ${
                activeChat === chat.id ? 'bg-slate-200' : ''
              } ${isSidebarCollapsed ? 'p-2' : 'p-2'}`}
            >
              {isSidebarCollapsed ? chat.title.charAt(0) : chat.title}
            </button>
          ))}
        </div>
        <div className="mt-auto w-full space-y-2 px-2 py-4">
          {['User', 'Settings', 'Logout'].map((item, index) => (
            <button
              key={item}
              onClick={item === 'Logout' ? handleLogout : () => router.push(`/${item.toLowerCase()}`)}
              className={`flex w-full items-center gap-x-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 focus:outline-none dark:text-slate-200 dark:hover:bg-slate-800 ${
                isSidebarCollapsed ? 'justify-center' : ''
              }`}
            >
              {index === 0 && <User size={20} />}
              {index === 1 && <Settings size={20} />}
              {index === 2 && <LogOut size={20} />}
              {!isSidebarCollapsed && <span>{item}</span>}
            </button>
          ))}
        </div>
      </div>
      <button 
        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        className="absolute -right-3 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full bg-slate-200 text-slate-600 hover:bg-slate-300 focus:outline-none dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
      >
        {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  );
};

export default Sidebar;