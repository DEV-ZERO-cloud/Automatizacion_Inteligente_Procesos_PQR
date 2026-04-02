import api from './api';
import type { DashboardStats, ReportByCategory, ReportByPriority } from '../types';

export const reportService = {
  async getDashboard(): Promise<DashboardStats> {
    const response = await api.get('/reports/dashboard');
    const payload = response.data?.data ?? {};
    return {
      total: payload.total_pqrs ?? 0,
      pendientes: payload.pendientes ?? 0,
      resueltas: payload.resueltas ?? 0,
      en_proceso: 0,
      tiempo_promedio: 0,
    };
  },
  async getByCategory(): Promise<ReportByCategory[]> {
    const response = await api.get('/reports/by-category');
    return response.data?.data ?? [];
  },
  async getByPriority(): Promise<ReportByPriority[]> {
    const response = await api.get('/reports/by-priority');
    return response.data?.data ?? [];
  },
};
