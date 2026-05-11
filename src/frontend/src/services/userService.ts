import api from './api';
import type { CreateUserRequest, RoleItem, UserUpdateRequest } from '../types';

export interface UserListItem {
  id: number;
  identificacion: string;
  nombre: string;
  correo: string;
  telefono?: string;
  rol_id: number;
  area_id: number;
  activo: boolean;
}

export const userService = {
  async getAll(): Promise<UserListItem[]> {
    const response = await api.get('/users');
    return response.data?.data ?? [];
  },

  async getSupervisors(): Promise<UserListItem[]> {
    const response = await api.get('/supervisors');
    return response.data?.data ?? [];
  },

  async create(payload: CreateUserRequest): Promise<{ id: number }> {
    const response = await api.post('/users/create', payload);
    return response.data?.data ?? { id: 0 };
  },

  async getRoles(): Promise<RoleItem[]> {
    const response = await api.get('/roles');
    return response.data?.data ?? [];
  },

  async update(payload: UserUpdateRequest): Promise<void> {
    await api.put('/users/update', payload);
  },

  async delete(userId: number): Promise<void> {
    await api.delete(`/users/delete/${userId}`);
  },
};
