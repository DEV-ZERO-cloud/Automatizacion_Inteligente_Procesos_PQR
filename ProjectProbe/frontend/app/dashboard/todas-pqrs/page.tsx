'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { pqrService, authService } from '@/lib/api';
import { PQR, User } from '@/lib/types';
import { FileText, Search, Filter, UserPlus } from 'lucide-react';

export default function TodasPqrsPage() {
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [supervisores, setSupervisores] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEstado, setFilterEstado] = useState('');
  const [filterTipo, setFilterTipo] = useState('');
  const [showAsignarModal, setShowAsignarModal] = useState(false);
  const [selectedPqr, setSelectedPqr] = useState<PQR | null>(null);
  const [asignando, setAsignando] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [pqrsData, supervisoresData] = await Promise.all([
        pqrService.getTodas(),
        authService.getUsuarios('supervisor'),
      ]);
      setPqrs(pqrsData);
      setSupervisores(supervisoresData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAsignar = async (supervisorId: number) => {
    if (!selectedPqr) return;
    setAsignando(true);
    try {
      await pqrService.asignarSupervisor(selectedPqr.id, supervisorId);
      setShowAsignarModal(false);
      setSelectedPqr(null);
      loadData();
    } catch (error) {
      console.error('Error assigning:', error);
    } finally {
      setAsignando(false);
    }
  };

  const filteredPqrs = pqrs.filter((pqr) => {
    const matchesSearch = pqr.titulo.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEstado = !filterEstado || pqr.estado === filterEstado;
    const matchesTipo = !filterTipo || pqr.tipo === filterTipo;
    return matchesSearch && matchesEstado && matchesTipo;
  });

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
        <h1 className="text-2xl font-bold text-gray-800">Todas las PQR's</h1>
        <p className="text-gray-500">Vista general de todas las solicitudes del sistema</p>
      </div>

      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative md:col-span-2">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Buscar por título..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-12"
            />
          </div>
          <select
            value={filterEstado}
            onChange={(e) => setFilterEstado(e.target.value)}
            className="input-field"
          >
            <option value="">Todos los estados</option>
            <option value="creado">Creadas</option>
            <option value="en_proceso">En Proceso</option>
            <option value="resuelto">Resueltas</option>
          </select>
          <select
            value={filterTipo}
            onChange={(e) => setFilterTipo(e.target.value)}
            className="input-field"
          >
            <option value="">Todos los tipos</option>
            <option value="peticion">Peticiones</option>
            <option value="queja">Quejas</option>
            <option value="reclamo">Reclamos</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>
      ) : filteredPqrs.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="w-16 h-16 text-gray mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No hay PQR's</h3>
          <p className="text-gray-500">Crea la primera solicitud del sistema</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPqrs.map((pqr) => (
            <div key={pqr.id} className="card">
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
              
              <div className="space-y-2 mb-4 text-sm">
                <p className="text-gray-500">
                  <span className="font-medium">Usuario:</span> {pqr.usuario_nombre}
                </p>
                <p className="text-gray-500">
                  <span className="font-medium">Fecha:</span> {formatDate(pqr.created_at)}
                </p>
                {pqr.supervisor_nombre ? (
                  <p className="text-primary-500">
                    <span className="font-medium">Supervisor:</span> {pqr.supervisor_nombre}
                  </p>
                ) : (
                  <p className="text-warning">
                    <span className="font-medium">Sin asignar</span>
                  </p>
                )}
              </div>

              {!pqr.supervisor_nombre && (
                <button
                  onClick={() => {
                    setSelectedPqr(pqr);
                    setShowAsignarModal(true);
                  }}
                  className="w-full btn-secondary flex items-center justify-center gap-2 text-sm"
                >
                  <UserPlus className="w-4 h-4" />
                  Asignar Supervisor
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {showAsignarModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Asignar Supervisor</h2>
            <p className="text-gray mb-4">
              Selecciona un supervisor para la PQR "#{selectedPqr?.id}"
            </p>
            <div className="space-y-2 max-h-60 overflow-y-auto mb-4">
              {supervisores.map((supervisor) => (
                <button
                  key={supervisor.id}
                  onClick={() => handleAsignar(supervisor.id)}
                  disabled={asignando}
                  className="w-full p-3 text-left rounded-xl border border-gray-200 hover:border-primary-500 hover:bg-primary-50 transition-all"
                >
                  <p className="font-medium text-gray-800">{supervisor.nombre}</p>
                  <p className="text-sm text-gray-500">{supervisor.email}</p>
                </button>
              ))}
            </div>
            <button
              onClick={() => {
                setShowAsignarModal(false);
                setSelectedPqr(null);
              }}
              className="w-full btn-secondary"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
