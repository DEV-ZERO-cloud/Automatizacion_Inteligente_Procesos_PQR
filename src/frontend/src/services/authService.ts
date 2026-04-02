import api from './api';
import type { LoginResponse } from '../types';

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post<{
      access_token: string;
      token_type: string;
      user_id: number;
      role: string;
    }>('/auth/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type,
      expires_in: 86400,
      user: {
        id: String(response.data.user_id),
        username: username,
        email: username,
        full_name: username.split('@')[0],
        rol_id: response.data.role,
        is_active: true,
        created_at: new Date().toISOString(),
      },
    };
  },
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore errors
    }
  },
};
