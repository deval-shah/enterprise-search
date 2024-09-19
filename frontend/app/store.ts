// store.ts
import { create } from 'zustand';
import { User } from 'firebase/auth';
import { auth } from './lib/firebase';
import { Message,ContextDetail } from './types';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware'

export interface AuthState {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  getAuthHeader: () => Promise<HeadersInit>;
}

interface UiState {
  isSidebarCollapsed: boolean;
  activeChat: string | null;
  setIsSidebarCollapsed: (isCollapsed: boolean) => void;
  setActiveChat: (chatId: string | null) => void;
}

interface FileUploadState {
    isUploading: boolean;
    uploadStatus: string | null;
    uploadedFiles: File[];
    setUploadedFiles: (files: File[]) => void;
    clearUploadedFiles: () => void;
    setIsUploading: (isUploading: boolean) => void;
    setUploadStatus: (status: string | null) => void;
    clearUploadStatus: () => void;
}

interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

interface ChatHistoryState {
  chats: Chat[];
  setChats: (chats: Chat[]) => void;
  addChat: (chat: Chat) => void;
}

interface ChatState {
    messages: Message[];
    input: string;
    isLoading: boolean;
    isTyping: boolean;
    isWaitingForResponse: boolean;
    metadata: any | null;
    fileUploadProgress: { [filename: string]: number };
    fileCount: number | 0;
    setMessages: (messages: Message[]) => void;
    addMessage: (message: Message) => void;
    setInput: (input: string) => void;
    setIsLoading: (isLoading: boolean) => void;
    updateLastMessage: (content: string, context?: ContextDetail[]) => void;
    setMetadata: (metadata: Record<string, any>) => void;
    setIsWaitingForResponse: (isWaiting: boolean) => void;
    clearMessages: () => void;
    setIsTyping: (isTyping: boolean) => void;
    updateFileUploadProgress: (filename: string, progress: number) => void;
    setFileCount: (fileCount: number) => void;
    clearFileCount: () => void;
}


export const useAuthStore = create<AuthState>()(
  subscribeWithSelector(
    persist(
      (set) => ({
      user: null,
      loading: true,
      setUser: async (user) => set({ user }),
      setLoading: (loading) => set({ loading }),
      getAuthHeader: async () => {
        const currentUser = auth.currentUser;
        if (!currentUser) {
          throw new Error('User not authenticated');
        }
        try {
          const token = await currentUser.getIdToken();
          return { 'Authorization': `Bearer ${token}` };
        } catch (error) {
          console.error('Error getting ID token:', error);
          throw new Error('Failed to get authentication token');
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
  )
);

export const useFileUploadStore = create<FileUploadState>()(
  persist(
    (set) => ({
      isUploading: false,
      uploadStatus: null,
      uploadedFiles: [],
      setUploadedFiles: (files) => set({ uploadedFiles: files }),
      clearUploadedFiles: () => set({ uploadedFiles: [] }),
      setIsUploading: (isUploading) => set({ isUploading }),
      setUploadStatus: (status) => set({ uploadStatus: status }),
      clearUploadStatus: () => set({ uploadStatus: null }),
    }),
    {
      name: 'file-upload-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      input: '',
      isLoading: false,
      isWaitingForResponse: false,
      metadata: null,
      isTyping: false,
      fileUploadProgress: {},
      fileCount: 0,
      setFileCount: (fileCount: number) => set({ fileCount }),
      setMessages: (messages) => set({ messages }),
      setMetadata: (metadata: Record<string, any>) => set({ metadata }),
      setIsTyping: (isTyping: boolean) => set({ isTyping }),
      setInput: (input) => set({ input }),
      setIsLoading: (isLoading) => set({ isLoading }),
      setIsWaitingForResponse: (isWaiting) => set({ isWaitingForResponse: isWaiting }),
      clearMessages: () => set({ messages: [] }),
      clearFileCount: () => set({ fileCount: 0 }),
      addMessage: (message: Message) => set((state) => ({
        messages: [...state.messages, message]
      })),
      updateLastMessage: (content: string) => set((state) => {
        const messages = [...state.messages];
        const lastMessageIndex = messages.length - 1;
        if (lastMessageIndex >= 0 && messages[lastMessageIndex].role === 'assistant') {
          messages[lastMessageIndex] = {
            ...messages[lastMessageIndex],
            content: messages[lastMessageIndex].content + content,
          };
        }
        return { messages };
      }),
      updateFileUploadProgress: (filename: string, progress: number) => 
        set((state) => ({
          fileUploadProgress: {
            ...state.fileUploadProgress,
            [filename]: progress
          }
        })),
    }),
    {
      name: 'chat-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

export const useChatHistoryStore = create<ChatHistoryState>((set) => ({
  chats: [],
  setChats: (chats) => set({ chats }),
  addChat: (chat) => set((state) => ({ chats: [...state.chats, chat] })),
}));

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      activeChat: null,
      setIsSidebarCollapsed: (isCollapsed) => set({ isSidebarCollapsed: isCollapsed }),
      setActiveChat: (chatId) => set({ activeChat: chatId }),
    }),
    {
      name: 'ui-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
