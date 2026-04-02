import api from './api';
import type { PQR, Classification } from '../types';

export const pqrService = {
  async getAll(filters?: {
    estado?: string;
    categoria?: string;
    prioridad?: string;
    area_id?: number;
    usuario_id?: number;
    search?: string;
  }): Promise<PQR[]> {
    const response = await api.get('/pqrs', { params: filters });
    return response.data?.data ?? [];
  },
  async getById(id: number): Promise<PQR> {
    const response = await api.get(`/pqrs/${id}`);
    return response.data?.data;
  },
  async create(data: Partial<PQR>): Promise<PQR> {
    const response = await api.post('/pqrs', data);
    return response.data?.data;
  },
  async update(id: number, data: Partial<PQR>): Promise<PQR> {
    const response = await api.put(`/pqrs/${id}`, data);
    return response.data?.data;
  },
  async delete(id: number): Promise<void> {
    await api.delete(`/pqrs/${id}`);
  },
  async getAllClassifications(): Promise<Classification[]> {
    const response = await api.get('/classifications');
    return response.data?.data ?? [];
  },
  async getClassification(pqrId: number): Promise<Classification> {
    const response = await api.get(`/classifications/pqr/${pqrId}`);
    return response.data?.data;
  },
  async validateClassification(
    data: {
      id: number;
      pqr_id: number;
      modelo_version: string;
      categoria_id: number;
      prioridad_id: number;
      confianza: number;
      origen: string;
      fue_corregida: boolean;
      validado_por?: number;
      created_at?: string;
    }
  ): Promise<Classification> {
    const response = await api.post('/classifications/validate', data);
    return response.data?.data;
  },
};
