'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { pqrService } from '@/lib/api';
import { ArrowLeft, FileText, Image, Upload, Send } from 'lucide-react';

export default function NuevaPqrPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    titulo: '',
    descripcion: '',
    tipo: 'peticion',
  });
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const pqr = await pqrService.crear(formData);
      
      if (files.length > 0) {
        await pqrService.subirArchivos(pqr.id, files);
      }
      
      router.push(`/dashboard/mis-pqrs/${pqr.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear la PQR');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      if (files.length + newFiles.length <= 3) {
        setFiles([...files, ...newFiles]);
      } else {
        setError('Máximo 3 archivos');
      }
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <div className="max-w-2xl mx-auto fade-in">
      <Link
        href="/dashboard/mis-pqrs"
        className="inline-flex items-center gap-2 text-gray hover:text-gray-800 mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver a Mis PQR's
      </Link>

      <div className="card">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Nueva PQR</h1>
        <p className="text-gray mb-8">Crea una nueva petición, queja o reclamo</p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="label-field">Tipo de solicitud *</label>
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: 'peticion', label: 'Petición', icon: FileText, color: 'blue' },
                { value: 'queja', label: 'Queja', icon: FileText, color: 'red' },
                { value: 'reclamo', label: 'Reclamo', icon: FileText, color: 'orange' },
              ].map((tipo) => (
                <button
                  key={tipo.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, tipo: tipo.value })}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    formData.tipo === tipo.value
                      ? `border-primary-500 bg-primary-50`
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="block text-sm font-medium">{tipo.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label-field">Título *</label>
            <input
              type="text"
              required
              value={formData.titulo}
              onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
              className="input-field"
              placeholder="Describe brevemente tu solicitud"
              maxLength={255}
            />
          </div>

          <div>
            <label className="label-field">Descripción *</label>
            <textarea
              required
              value={formData.descripcion}
              onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
              className="input-field min-h-[150px] resize-y"
              placeholder="Explica en detalle tu solicitud..."
            />
          </div>

          <div>
            <label className="label-field">Archivos adjuntos (máx. 3)</label>
            <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:border-primary-300 transition-colors">
              <input
                type="file"
                id="files"
                multiple
                accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="files" className="cursor-pointer">
                <Upload className="w-10 h-10 text-gray mx-auto mb-3" />
                <p className="text-gray-500">Haz clic o arrastra archivos aquí</p>
                <p className="text-xs text-gray mt-1">JPG, PNG, PDF o DOC (máx. 10MB)</p>
              </label>
            </div>

            {files.length > 0 && (
              <div className="mt-4 space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Image className="w-5 h-5 text-gray-500" />
                      <span className="text-sm text-gray-800">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Enviar Solicitud
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
