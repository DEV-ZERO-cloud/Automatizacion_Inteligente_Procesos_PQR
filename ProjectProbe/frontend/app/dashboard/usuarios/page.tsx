'use client';

import { useEffect, useState } from 'react';
import { authService } from '@/lib/api';
import { User } from '@/lib/types';
import { User as UserIcon, Plus, Shield, Mail, Calendar } from 'lucide-react';

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nombre: '',
  });
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadUsuarios();
  }, []);

  const loadUsuarios = async () => {
    try {
      const data = await authService.getUsuarios();
      setUsuarios(data);
    } catch (error) {
      console.error('Error loading usuarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSupervisor = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError('');
    try {
      await authService.registerSupervisor(formData);
      setShowModal(false);
      setFormData({ email: '', password: '', nombre: '' });
      loadUsuarios();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear supervisor');
    } finally {
      setCreating(false);
    }
  };

  const getRolLabel = (rol: string) => {
    const labels: Record<string, string> = {
      usuario: 'Usuario',
      supervisor: 'Supervisor',
      operador: 'Operador',
    };
    return labels[rol] || rol;
  };

  const getRolBadgeClass = (rol: string) => {
    const classes: Record<string, string> = {
      usuario: 'bg-blue-100 text-blue-700',
      supervisor: 'bg-warning/20 text-yellow-700',
      operador: 'bg-primary-100 text-primary-700',
    };
    return classes[rol] || '';
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const usuariosPorRol = {
    operador: usuarios.filter((u) => u.rol === 'operador'),
    supervisor: usuarios.filter((u) => u.rol === 'supervisor'),
    usuario: usuarios.filter((u) => u.rol === 'usuario'),
  };

  return (
    <div className="max-w-6xl mx-auto fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestión de Usuarios</h1>
          <p className="text-gray-500">Administra los usuarios del sistema</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Nuevo Supervisor
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>
      ) : (
        <div className="space-y-8">
          <UserSection
            title="Operadores"
            users={usuariosPorRol.operador}
            icon={Shield}
            color="primary"
            getRolBadgeClass={getRolBadgeClass}
            getRolLabel={getRolLabel}
            formatDate={formatDate}
          />
          <UserSection
            title="Supervisores"
            users={usuariosPorRol.supervisor}
            icon={UserIcon}
            color="warning"
            getRolBadgeClass={getRolBadgeClass}
            getRolLabel={getRolLabel}
            formatDate={formatDate}
          />
          <UserSection
            title="Usuarios"
            users={usuariosPorRol.usuario}
            icon={UserIcon}
            color="blue"
            getRolBadgeClass={getRolBadgeClass}
            getRolLabel={getRolLabel}
            formatDate={formatDate}
          />
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Nuevo Supervisor</h2>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateSupervisor} className="space-y-4">
              <div>
                <label className="label-field">Nombre</label>
                <input
                  type="text"
                  required
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  className="input-field"
                  placeholder="Nombre completo"
                />
              </div>
              <div>
                <label className="label-field">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="correo@ejemplo.com"
                />
              </div>
              <div>
                <label className="label-field">Contraseña</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-field"
                  placeholder="••••••••"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={creating}
                  className="btn-primary flex-1"
                >
                  {creating ? 'Creando...' : 'Crear Supervisor'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setError('');
                    setFormData({ email: '', password: '', nombre: '' });
                  }}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function UserSection({
  title,
  users,
  icon: Icon,
  color,
  getRolBadgeClass,
  getRolLabel,
  formatDate,
}: any) {
  const colorClasses: Record<string, string> = {
    primary: 'bg-primary-100 text-primary-600',
    warning: 'bg-warning/20 text-yellow-700',
    blue: 'bg-blue-100 text-blue-600',
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold text-gray-800">{title}</h2>
          <p className="text-sm text-gray-500">{users.length} usuario{users.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      {users.length === 0 ? (
        <p className="text-gray text-center py-4">No hay usuarios</p>
      ) : (
        <div className="space-y-3">
          {users.map((user) => (
            <div
              key={user.id}
              className="flex items-center gap-4 p-3 bg-gray-50 rounded-xl"
            >
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm">
                <UserIcon className="w-5 h-5 text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-800 truncate">{user.nombre}</p>
                  <span className={`status-badge ${getRolBadgeClass(user.rol)}`}>
                    {getRolLabel(user.rol)}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    {user.email}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(user.created_at)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
