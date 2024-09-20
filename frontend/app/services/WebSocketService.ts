import { User } from 'firebase/auth';
import { useAuthStore, AuthState } from '../store';
import { useChatStore } from '../store';
import { getCookie } from '../utils/cookies';
import { WSQueryMessage, WSResponse } from '../websocket.types';
class WebSocketService {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectInterval = 5000;
    private user: User | null = null;
    private sessionId: string | null = null;

    //constructor(private getAuthHeader: () => Promise<HeadersInit>) {}

    public reconnect = async () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          console.log(`Attempting to reconnect (attempt ${this.reconnectAttempts + 1})`);
          this.reconnectAttempts++;
          this.connect(this.user!);
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
      }
    };

    async connect(user: User): Promise<string> {
        this.user = user;
        if (this.socket?.readyState === WebSocket.OPEN) return this.sessionId || '';
    
        const { getAuthHeader } = useAuthStore.getState() as AuthState;
        let headers;
        try {
          headers = await getAuthHeader();
        } catch (error) {
          console.error('Failed to get auth header:', error);
          // Retry after a short delay
          await new Promise(resolve => setTimeout(resolve, 1000));
          return this.connect(user);
        }

        const token = (headers as Record<string, string>)['Authorization']?.split(' ')[1];
        const wsUrl = new URL('/ws', process.env.NEXT_PUBLIC_API_URL);
        const sessionId = getCookie('session_id'); // Implement getCookie function
        
        console.log("WebSocket URL:", wsUrl.toString());
        wsUrl.protocol = wsUrl.protocol.replace('https', 'ws');

        this.socket = new WebSocket(wsUrl.toString());

        this.socket.onopen = () => {
            this.reconnectAttempts = 0;
            if (this.socket?.readyState === WebSocket.OPEN) {
              if (sessionId){
                this.socket.send(JSON.stringify({ type: 'auth', token: `Bearer ${token}`, session_id: sessionId }));
              }
              else {
                this.socket?.send(JSON.stringify({ type: 'auth', token: `Bearer ${token}` }));
              }
            }
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            this.handleDisconnection;
        };
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return new Promise<string>((resolve, reject) => {
          if (!this.socket) return reject('Socket is null');

          this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'authentication_success') {
              this.sessionId = data.session_id;
              resolve(this.sessionId || '');
            } else if (data.type === 'authentication_failed') {
              reject(data.content);
            }
          };
        });
      }

  private handleDisconnection = () => {
    if (this.user && this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        if (this.user) {
          this.reconnect();
        }
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached or no user');
      // Dispatch a custom event when max reconnection attempts are reached
      window.dispatchEvent(new Event('websocket_disconnect'));
    }
  };

  async sendMessage(message: { query: string, files?: File[] }) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not open');
      return;
    }
    const { addMessage, setIsWaitingForResponse } = useChatStore.getState();
    
    let fileContents: { name: string, content: string }[] = [];
    if (message.files && message.files.length > 0) {
      fileContents = await Promise.all(message.files.map(async (file) => {
        return new Promise<{ name: string, content: string }>((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64Content = e.target?.result as string;
            resolve({
              name: file.name,
              content: base64Content.split(',')[1] // Remove the data URL prefix
            });
          };
          reader.readAsDataURL(file);
        });
      }));
    }

    const wsMessage: WSQueryMessage = {
      type: 'query',
      query: message.query,
      stream: true,
      files: fileContents,
      session_id: this.sessionId || ''
    };

    addMessage({ role: 'user', content: message.query });
    setIsWaitingForResponse(true);

    console.log('WebSocket sending message:', JSON.stringify(wsMessage));
    this.socket.send(JSON.stringify(wsMessage));
  }

    onMessage(callback: (data: WSResponse) => void) {
      if (this.socket) {
        this.socket.onmessage = (event) => {
          const data: WSResponse = JSON.parse(event.data);
          const { addMessage, updateLastMessage, setIsWaitingForResponse, setMetadata } = useChatStore.getState();
          console.log('WebSocket response message:', JSON.stringify(data));
          switch (data.type) {
            case 'metadata':
              if (typeof data.content === 'object') {
                setMetadata(data.content);
                // Add a new assistant message with empty content but with context
                addMessage({ role: 'assistant', content: '', context: data.content.context });
              }
              break;
            case 'chunk':
              if (typeof data.content === 'string') {
                console.log('Received chunk:', data.content);
                updateLastMessage(data.content);
              }
              break;
            case 'end_stream':
              setIsWaitingForResponse(false);
              break;
            case 'error':
              console.error('WebSocket error:', data.content);
              if (typeof data.content === 'string') {
                addMessage({ role: 'system', content: `Error: ${data.content}` });
              }
              break;
          }
          callback(data);
        };
      }
    }

  close() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export default WebSocketService;
