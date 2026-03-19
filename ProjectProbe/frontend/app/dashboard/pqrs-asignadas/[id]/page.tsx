'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { pqrService } from '@/lib/api';
import { PQR } from '@/lib/types';
import { ArrowLeft, Clock, User, FileText, Paperclip, MessageSquare, Send } from 'lucide-react';

export default function DetallePqrSupervisorPage() {
  const router = useRouter();
  const params = useParams();
  const [pqr, setPqr] = useState<PQR | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [comentario, setComentario] = useState('');

  useEffect(() => {
    const loadPqr = async () => {
      try {
        const data = await pqrService.getDetalle(Number(params.id));
        setPqr(data);
      } catch (error) {
        console.error('Error loading PQR:', error);
        router.push('/dashboard/pqrs-asignadas');
      } finally {
        setLoading(false);
      }
    };
    loadPqr();
  }, [params.id, router]);

  const handleActualizarEstado = async (nuevoEstado: string) => {
    if (!pqr) return;
    setUpdating(true);
    try {
      await pqrService.actualizarEstado(pqr.id, {
        estado: nuevoEstado,
        comentario: comentario || undefined,
      });
      setComentario('');
      const data = await pqrService.getDetalle(pqr.id);
      setPqr(data);
    } catch (error) {
      console.error('Error updating:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleAgregarComentario = async () => {
    if (!pqr || !comentario.trim()) return;
    setUpdating(true);
    try {
      await pqrService.agregarComentario(pqr.id, comentario);
      setComentario('');
      const data = await pqrService.getDetalle(pqr.id);
      setPqr(data);
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setUpdating(false);
    }
  };

  const getTipoLabel = (tipo: string) => {
    return tipo.charAt(0).toUpperCase() + tipo.slice(1);
  };

  const getEstadoLabel = (estado: string) => {
    const labels: Record<string, string> = {
      creado: 'Creada',
      en_proceso: 'En Proceso',
      resuelto: 'Resuelta',
    };
    return labels[estado] || estado;
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!pqr) return null;

  return (
    <div className="max-w-4xl mx-auto fade-in">
      <Link
        href="/dashboard/pqrs-asignadas"
        className="inline-flex items-center gap-2 text-gray hover:text-gray-800 mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver a PQR's Asignadas
      </Link>

      <div className="card mb-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className={`status-badge ${`tipo-${pqr.tipo}`}`}>
                {getTipoLabel(pqr.tipo)}
              </span>
              <span className={`status-badge ${`status-${pqr.estado}`}`}>
                {getEstadoLabel(pqr.estado)}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-800">{pqr.titulo}</h1>
            <p className="text-gray-500">PQR #{pqr.id}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Usuario</p>
              <p className="font-semibold text-gray-800">{pqr.usuario_nombre}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Fecha de creación</p>
              <p className="font-semibold text-gray-800">{formatDate(pqr.created_at)}</p>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-100 pt-6">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-500" />
            Descripción
          </h3>
          <p className="text-gray leading-relaxed">{pqr.descripcion}</p>
        </div>

        {pqr.archivos && pqr.archivos.length > 0 && (
          <div className="border-t border-gray-100 pt-6 mt-6">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Paperclip className="w-5 h-5 text-primary-500" />
              Archivos adjuntos ({pqr.archivos.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {pqr.archivos.map((archivo) => (
                <a
                  key={archivo.id}
                  href={`${process.env.NEXT_PUBLIC_API_URL}/uploads/${archivo.filename}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
                >
                  <Paperclip className="w-4 h-4" />
                  {archivo.filename}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="card mb-6">
        <h3 className="font-semibold text-gray-800 mb-4">Actualizar Estado</h3>
        <div className="flex flex-wrap gap-3 mb-4">
          <button
            onClick={() => handleActualizarEstado('en_proceso')}
            disabled={updating || pqr.estado === 'en_proceso'}
            className={`px-4 py-2 rounded-xl font-medium transition-all ${
              pqr.estado === 'en_proceso'
                ? 'bg-warning/20 text-yellow-700 cursor-not-allowed'
                : 'bg-warning text-yellow-800 hover:bg-warning/80'
            }`}
          >
            En Proceso
          </button>
          <button
            onClick={() => handleActualizarEstado('resuelto')}
            disabled={updating || pqr.estado === 'resuelto'}
            className={`px-4 py-2 rounded-xl font-medium transition-all ${
              pqr.estado === 'resuelto'
                ? 'bg-success/20 text-success cursor-not-allowed'
                : 'bg-success text-white hover:bg-success/80'
            }`}
          >
            Resuelta
          </button>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            placeholder="Agregar comentario (opcional)..."
            className="input-field flex-1"
          />
          <button
            onClick={handleAgregarComentario}
            disabled={updating || !comentario.trim()}
            className="btn-primary flex items-center gap-2"
          >
            <MessageSquare className="w-5 h-5" />
            Comentar
          </button>
        </div>
      </div>

      {pqr.historial && pqr.historial.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-primary-500" />
            Historial
          </h3>
          <div className="space-y-4">
            {pqr.historial.map((item) => (
              <div key={item.id} className="flex gap-4">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-800">{item.accion}</span>
                    <span className="text-sm text-gray-500">{formatDate(item.created_at)}</span>
                  </div>
                  {item.comentario && (
                    <p className="text-gray text-sm mb-1">{item.comentario}</p>
                  )}
                  <p className="text-xs text-gray-500">Por: {item.usuario_nombre}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
