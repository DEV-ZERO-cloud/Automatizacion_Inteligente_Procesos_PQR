import api from './api';
import type { LoginResponse, RegisterRequest } from '../types';

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post<{
      success?: boolean;
      message?: string;
      data?: {
        access_token: string;
        token_type: string;
        user_id: number;
        role: string;
      };
      access_token?: string;
      token_type?: string;
      user_id?: number;
      role?: string;
    }>('/auth/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const payload = response.data?.data
      ? response.data.data
      : {
          access_token: response.data.access_token as string,
          token_type: response.data.token_type as string,
          user_id: response.data.user_id as number,
          role: response.data.role as string,
        };

    return {
      access_token: payload.access_token,
      token_type: payload.token_type,
      expires_in: 86400,
      user: {
        id: String(payload.user_id),
        username: username,
        email: username,
        full_name: username.split('@')[0],
        rol_id: payload.role,
        is_active: true,
        created_at: new Date().toISOString(),
      },
    };
  },
  async register(payload: RegisterRequest): Promise<LoginResponse> {
    const response = await api.post<{
      success?: boolean;
      message?: string;
      data?: {
        access_token: string;
        token_type: string;
        user_id: number;
        role: string;
      };
      access_token?: string;
      token_type?: string;
      user_id?: number;
      role?: string;
    }>('/auth/register', payload);

    const data = response.data?.data
      ? response.data.data
      : {
          access_token: response.data.access_token as string,
          token_type: response.data.token_type as string,
          user_id: response.data.user_id as number,
          role: response.data.role as string,
        };

    return {
      access_token: data.access_token,
      token_type: data.token_type,
      expires_in: 86400,
      user: {
        id: String(data.user_id),
        username: payload.correo,
        email: payload.correo,
        full_name: payload.nombre,
        rol_id: data.role,
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
