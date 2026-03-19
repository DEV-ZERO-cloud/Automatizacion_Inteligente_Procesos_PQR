'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { pqrService } from '@/lib/api';
import { PQR } from '@/lib/types';
import { FileText, Search } from 'lucide-react';

export default function PqrsAsignadasPage() {
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const loadPqrs = async () => {
      try {
        const data = await pqrService.getAsignadas();
        setPqrs(data);
      } catch (error) {
        console.error('Error loading PQRs:', error);
      } finally {
        setLoading(false);
      }
    };
    loadPqrs();
  }, []);

  const filteredPqrs = pqrs.filter((pqr) =>
    pqr.titulo.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="max-w-6xl mx-auto fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-800">PQR's Asignadas</h1>
        <p className="text-gray-500">Gestiona las PQR's que están asignadas a ti</p>
      </div>

      <div className="card mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar por título..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-12"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>
      ) : filteredPqrs.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="w-16 h-16 text-gray mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No hay PQR's asignadas</h3>
          <p className="text-gray-500">Las PQR's que te asignen aparecerán aquí</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPqrs.map((pqr) => (
            <Link key={pqr.id} href={`/dashboard/pqrs-asignadas/${pqr.id}`} className="card hover:scale-105 transition-transform">
              <div className="flex items-start justify-between mb-4">
                <span className={`status-badge ${`tipo-${pqr.tipo}`}`}>
                  {getTipoLabel(pqr.tipo)}
                </span>
                <span className={`status-badge ${`status-${pqr.estado}`}`}>
                  {getEstadoLabel(pqr.estado)}
                </span>
              </div>
              <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2">{pqr.titulo}</h3>
              <p className="text-sm text-gray mb-4">#{pqr.id}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">{formatDate(pqr.created_at)}</span>
                <span className="text-primary-500 font-medium">Ver detalles →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
