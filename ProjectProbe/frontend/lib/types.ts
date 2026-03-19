export interface User {
  id: number;
  email: string;
  nombre: string;
  rol: 'usuario' | 'supervisor' | 'operador';
  is_active: number;
  created_at: string;
}

export interface PQR {
  id: number;
  titulo: string;
  descripcion?: string;
  tipo: 'peticion' | 'queja' | 'reclamo';
  estado: 'creado' | 'en_proceso' | 'resuelto';
  usuario_id: number;
  supervisor_id?: number;
  created_at: string;
  updated_at: string;
  usuario_nombre?: string;
  supervisor_nombre?: string;
  archivos?: Archivo[];
  historial?: Historial[];
}

export interface Archivo {
  id: number;
  filename: string;
  filepath: string;
  mimetype?: string;
  created_at: string;
}

export interface Historial {
  id: number;
  accion: string;
  comentario?: string;
  created_at: string;
  usuario_nombre?: string;
}

export interface Estadisticas {
  total: number;
  creados: number;
  en_proceso: number;
  resueltos: number;
  por_tipo: {
    peticion: number;
    queja: number;
    reclamo: number;
  };
}
