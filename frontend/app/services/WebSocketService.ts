import { User } from 'firebase/auth';
import { useAuthStore, AuthState } from '../store';
import { useChatStore } from '../store';
import { getCookie } from '../utils/cookies';

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
        wsUrl.protocol = wsUrl.protocol.replace('http', 'ws');

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
  async sendMessage(message: { query: string, files?: { name: string, file: File }[] }) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not open');
      return;
    }
    const { addMessage, setIsWaitingForResponse } = useChatStore.getState();
    addMessage({ role: 'user', content: message.query });
    setIsWaitingForResponse(true);

    console.log('WebSocket sending message:', JSON.stringify({
      type: 'query',
      query: message.query,
      stream: true,
      session_id: this.sessionId,
      files: message.files ? message.files.map(file => ({ name: file.name })) : []
    }));

    if (message.files && message.files.length > 0) {
      for (const { name, file } of message.files) {
        console.log(`Preparing to send file: ${name}, size: ${file.size} bytes`);
        const buffer = await file.arrayBuffer();
        // Send file metadata first
        this.socket.send(JSON.stringify({ type: 'file_metadata', name, size: file.size }));
        // Then send the file content
        this.socket.send(buffer);
        await new Promise<void>(resolve => {
          const checkBufferedAmount = () => {
            if (this.socket!.bufferedAmount === 0) {
              console.log(`File sent: ${name}`);
              resolve();
            } else {
              setTimeout(checkBufferedAmount, 100);
            }
          };
          checkBufferedAmount();
        });
      }
    }

    // Send query message
    this.socket.send(JSON.stringify({
      type: 'query',
      query: message.query,
      stream: true,
      session_id: this.sessionId,
      files: message.files ? message.files.map(file => ({ name: file.name })) : []
    }));
  }

    onMessage(callback: (data: any) => void) {
      if (this.socket) {
          this.socket.onmessage = (event) => {
              const data = JSON.parse(event.data);
              const { updateLastMessage, setIsWaitingForResponse, addMessage } = useChatStore.getState();

              switch (data.type) {
                  case 'chunk':
                      updateLastMessage(data.content);
                      break;
                  case 'metadata':
                      // Handle metadata (you might want to store this in the chat store)
                      break;
                  case 'end_stream':
                      setIsWaitingForResponse(false);
                      break;
                  case 'error':
                      console.error('WebSocket error:', data.content);
                      addMessage({ role: 'system', content: `Error: ${data.content}` });
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
