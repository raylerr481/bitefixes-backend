export interface PythonFile {
  name: string;
  path: string;
  content: string;
  description: string;
  language: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot' | 'system';
  text: string;
  timestamp: Date;
  isToolCall?: boolean;
  toolName?: string;
  toolArgs?: string;
  toolResult?: string;
}

export interface ClientRecord {
  id: string;
  nombre: string;
  whatsapp: string;
  direccion: string;
  created_at?: string;
}

export interface TicketRecord {
  id: string;
  created_at: string;
  categoria: 'Hardware' | 'Software' | 'Redes' | 'Comercial' | 'Otro';
  cliente_id: string;
  descripcion: string;
  estatus: 'Abierto' | 'En Proceso' | 'Resuelto';
}

export interface DeveloperLog {
  id: string;
  timestamp: string;
  source: 'whatsapp' | 'gemini' | 'supabase' | 'fastapi';
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  payload?: string;
}
