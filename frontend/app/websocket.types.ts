// app/websocket.types.ts

export interface WSQueryMessage {
  type: 'query';
  query: string;
  stream: boolean;
  files: Array<{ name: string; content: string }>;
  session_id: string;
}

export interface WSResponse {
  type: 'chunk' | 'metadata' | 'end_stream' | 'error';
  content: string | Record<string, any>;
}