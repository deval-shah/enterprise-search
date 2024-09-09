// app/types.ts

export interface ContextDetail {
    file_name: string;
    file_path: string;
    last_modified: string;
    document_id: string;
  }
  
  export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    context?: ContextDetail[];
    files?:  { name: string }[];
  }

  export interface AttachedFile extends File {
    preview?: string;
  }