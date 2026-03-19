import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    formData.append('grant_type', 'password');
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
    });
    return response.data;
  },
  register: async (data: { email: string; password: string; nombre: string }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  getUsuarios: async (rol?: string) => {
    const response = await api.get('/auth/usuarios', { params: { rol } });
    return response.data;
  },
  registerSupervisor: async (data: { email: string; password: string; nombre: string }) => {
    const response = await api.post('/auth/register/supervisor', data);
    return response.data;
  },
};

export const pqrService = {
  crear: async (data: { titulo: string; descripcion: string; tipo: string }) => {
    const response = await api.post('/pqr', data);
    return response.data;
  },
  getMisPqrs: async () => {
    const response = await api.get('/pqr/mis-pqrs');
    return response.data;
  },
  getAsignadas: async () => {
    const response = await api.get('/pqr/asignadas');
    return response.data;
  },
  getTodas: async (params?: { estado?: string; tipo?: string }) => {
    const response = await api.get('/pqr/todas', { params });
    return response.data;
  },
  getDetalle: async (id: number) => {
    const response = await api.get(`/pqr/${id}`);
    return response.data;
  },
  actualizarEstado: async (id: number, data: { estado: string; comentario?: string }) => {
    const response = await api.put(`/pqr/${id}/estado`, data);
    return response.data;
  },
  agregarComentario: async (id: number, comentario: string) => {
    const response = await api.put(`/pqr/${id}/comentario`, null, {
      params: { comentario },
    });
    return response.data;
  },
  asignarSupervisor: async (pqrId: number, supervisorId: number) => {
    const response = await api.put(`/pqr/${pqrId}/asignar`, { supervisor_id: supervisorId });
    return response.data;
  },
  subirArchivos: async (pqrId: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await api.post(`/pqr/${pqrId}/archivos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getEstadisticas: async () => {
    const response = await api.get('/pqr/estadisticas/dashboard');
    return response.data;
  },
};

export default api;
