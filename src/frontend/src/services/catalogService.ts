import api from './api';
import type { Category, Priority, Area } from '../types';

export const catalogService = {
  async getCategories(): Promise<Category[]> {
    const response = await api.get('/categories');
    return response.data?.data ?? [];
  },
  async getPriorities(): Promise<Priority[]> {
    const response = await api.get('/priorities');
    return response.data?.data ?? [];
  },
  async getAreas(): Promise<Area[]> {
    const response = await api.get('/areas');
    return response.data?.data ?? [];
  },
};
