import api from './api';

export interface DebugStatus {
  embedding_model: string;
  embedding_ready: boolean;
  rules_count: number;
  confidence_threshold: number;
  classifiers: {
    category: { ready: boolean; classes: string[] };
    priority: { ready: boolean; classes: string[] };
  };
  active_mode: string;
}

export interface TrainingCsv {
  filename: string;
  path: string;
  size_bytes: number;
  rows: number;
  modified: number;
}

export interface UploadResult {
  success: boolean;
  filename: string;
  path: string;
  size_bytes: number;
  rows: number;
  columns: string[];
  missing_columns: string[];
  valid: boolean;
}

export interface TrainResult {
  status: string;
  samples: number;
  models: Record<string, string>;
}

export interface CsvPreview {
  filename: string;
  columns: string[];
  preview: Record<string, string>[];
  total_previewed: number;
}

export const iaService = {
  async getDebugStatus(): Promise<DebugStatus> {
    const res = await api.get('/debug/status');
    return res.data;
  },

  async reloadRules(): Promise<{ success: boolean; rules_count: number; message: string }> {
    const res = await api.post('/reload_rules');
    return res.data;
  },

  async reloadModels(): Promise<{ success: boolean; models_ready: { category: boolean; priority: boolean }; message: string }> {
    const res = await api.post('/reload_models');
    return res.data;
  },

  async train(csvPath: string, target: string = 'all', minPerClass: number = 5): Promise<TrainResult> {
    const res = await api.post('/train', null, {
      params: { csv_path: csvPath, target, min_per_class: minPerClass },
    });
    return res.data;
  },

  async listCsvFiles(): Promise<TrainingCsv[]> {
    const res = await api.get('/training/csv/list');
    return res.data.files;
  },

  async uploadCsv(file: File): Promise<UploadResult> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/training/csv/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async previewCsv(filename: string): Promise<CsvPreview> {
    const res = await api.get(`/training/csv/${filename}/preview`);
    return res.data;
  },
};
