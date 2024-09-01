import { User } from 'firebase/auth';

class WebSocketService {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectInterval = 5000;
    private user: User | null = null;
    private sessionId: string | null = null;

    constructor(private getAuthHeader: () => Promise<HeadersInit>) {}

    async connect(user: User) {
        
        this.user = user;
        if (this.socket?.readyState === WebSocket.OPEN) return;
    
        const headers = await this.getAuthHeader();
        const token = (headers as Record<string, string>)['Authorization']?.split(' ')[1];

        const wsUrl = new URL('/ws', process.env.NEXT_PUBLIC_API_URL);
        console.log("WebSocket URL:", wsUrl.toString());
        wsUrl.protocol = wsUrl.protocol.replace('http', 'ws');

        this.socket = new WebSocket(wsUrl.toString());

        this.socket.onopen = () => {
            this.reconnectAttempts = 0;
            this.socket?.send(JSON.stringify({ type: 'auth', token: `Bearer ${token}` }));
        };
    
        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            this.handleDisconnection;
        };
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

    return new Promise((resolve, reject) => {
      if (!this.socket) return reject('Socket is null');
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'authentication_success') {
          this.sessionId = data.session_id;
          resolve(this.sessionId);
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
          this.connect(this.user);
        }
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached or no user');
    }
  };

  sendMessage(message: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      const messageWithSession = {
        ...message,
        session_id: this.sessionId
      };
      if (messageWithSession.files && messageWithSession.files.length > 0) {
        messageWithSession.files = messageWithSession.files.map((file: string) => file);
      } else {
        messageWithSession.files = []; // Ensure we always send an empty array if no files
      }
      console.log('Sending message:', messageWithSession);
      this.socket.send(JSON.stringify(messageWithSession));
    } else {
      console.error('WebSocket is not open');
    }
  }

  onMessage(callback: (data: any) => void) {
    if (this.socket) {
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
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
