export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  rol_id: string;
  is_active: boolean;
  created_at: string;
}

export interface PQR {
  id: number;
  titulo: string;
  descripcion: string;
  tipo: 'peticion' | 'queja' | 'reclamo' | string;
  estado: 'registrada' | 'en_proceso' | 'resuelta' | 'cerrada' | 'pendiente' | string;
  categoria?: string;
  prioridad?: string;
  usuario_id?: number;
  operador_id?: number;
  supervisor_id?: number;
  area_id?: number;
  created_at?: string;
  updated_at?: string;
  usuario_nombre?: string;
}

export interface Classification {
  id: string;
  pqr_id: string;
  modelo_version: string;
  categoria_id: string;
  prioridad_id: string;
  categoria_nombre?: string;
  prioridad_nombre?: string;
  confianza: number;
  origen: 'MANUAL' | 'IA';
  fue_corregida: boolean;
  validado_por?: string;
  validado_por_nombre?: string;
  created_at: string;
}

export interface Category {
  id: string;
  nombre: string;
  descripcion: string;
}

export interface Priority {
  id: string;
  nombre: string;
  nivel: number;
}

export interface Area {
  id: string;
  nombre: string;
  descripcion: string;
}

export interface DashboardStats {
  total: number;
  pendientes: number;
  resueltas: number;
  en_proceso: number;
  tiempo_promedio: number;
}

export interface ReportByCategory {
  categoria: string;
  cantidad: number;
  porcentaje: number;
}

export interface ReportByPriority {
  prioridad: string;
  cantidad: number;
  porcentaje: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export type Role = 'admin' | 'supervisor' | 'agente' | 'usuario';
