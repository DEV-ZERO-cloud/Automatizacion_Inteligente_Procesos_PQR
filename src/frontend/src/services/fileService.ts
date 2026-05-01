import api from './api';
import type { PQRFile } from '../types';

export const fileService = {
  async uploadToPqr(pqrId: number, file: File): Promise<PQRFile> {
    const formData = new FormData();
    formData.append('pqr_id', String(pqrId));
    formData.append('file', file);

    const response = await api.post('/archivos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data?.data;
  },

  async getByPqr(pqrId: number): Promise<PQRFile[]> {
    const response = await api.get(`/archivos/pqr/${pqrId}`);
    const data = response.data?.data;
    if (!data) {
      return [];
    }
    return Array.isArray(data) ? data : [data];
  },

  async getFileBlob(fileId: number): Promise<Blob> {
    const response = await api.get(`/archivos/${fileId}/content`, {
      responseType: 'blob',
    });
    return response.data;
  },
};