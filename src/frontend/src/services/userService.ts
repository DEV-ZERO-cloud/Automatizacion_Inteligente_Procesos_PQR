import api from './api';

export interface UserListItem {
  id: number;
  nombre: string;
  correo: string;
  rol_id: number;
  area_id: number;
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
};
