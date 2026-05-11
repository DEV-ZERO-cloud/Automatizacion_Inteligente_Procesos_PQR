import { useEffect, useMemo, useState } from 'react';
import { catalogService } from '../services/catalogService';
import { userService, type UserListItem } from '../services/userService';
import type { RoleItem } from '../types';

const roleById: Record<number, string> = {
  1: 'Administrador',
  2: 'Supervisora',
  3: 'Agente',
  4: 'Usuario',
  5: 'Operador',
  6: 'Gerente',
};

export function GestionUsuarios() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [areas, setAreas] = useState<{ id: string; nombre: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [deletingUser, setDeletingUser] = useState<UserListItem | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const [form, setForm] = useState({
    identificacion: '',
    nombre: '',
    correo: '',
    telefono: '',
    contrasena: '',
    rol_id: '',
    area_id: '',
  });

  const areaById = useMemo(() => new Map(areas.map((a) => [Number(a.id), a.nombre])), [areas]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [usersData, rolesData, areasData] = await Promise.all([
          userService.getAll(),
          userService.getRoles(),
          catalogService.getAreas(),
        ]);
        if (!mounted) return;
        setRoles(rolesData);
        setAreas(areasData);
        setUsers(usersData);
      } catch {
        if (mounted) setUsers([]);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  const filteredUsers = useMemo(() => {
    let result = users;
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((u) =>
        u.nombre.toLowerCase().includes(q) ||
        u.correo.toLowerCase().includes(q) ||
        u.identificacion.toLowerCase().includes(q)
      );
    }
    if (roleFilter) {
      result = result.filter((u) => u.rol_id === Number(roleFilter));
    }
    return result;
  }, [users, search, roleFilter]);

  const totalUsers = users.length;
  const visibleCount = filteredUsers.length;

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(visibleCount / pageSize));
  const paginatedUsers = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredUsers.slice(start, start + pageSize);
  }, [filteredUsers, currentPage]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [search, roleFilter]);

  const resetForm = () => {
    setForm({ identificacion: '', nombre: '', correo: '', telefono: '', contrasena: '', rol_id: '', area_id: '' });
    setError('');
  };

  const handleOpenCreate = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const handleOpenEdit = (u: UserListItem) => {
    setEditingUser(u);
    setForm({
      identificacion: u.identificacion,
      nombre: u.nombre,
      correo: u.correo,
      telefono: u.telefono ?? '',
      contrasena: '',
      rol_id: String(u.rol_id),
      area_id: String(u.area_id),
    });
    setError('');
    setShowEditModal(true);
  };

  const handleOpenDelete = (u: UserListItem) => {
    setDeletingUser(u);
    setError('');
    setShowDeleteModal(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!form.identificacion || !form.nombre || !form.correo || !form.contrasena || !form.rol_id || !form.area_id) {
      setError('Completa todos los campos obligatorios.');
      return;
    }
    if (form.contrasena.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    setLoading(true);
    try {
      await userService.create({
        identificacion: form.identificacion.trim(),
        nombre: form.nombre.trim(),
        correo: form.correo.trim().toLowerCase(),
        telefono: form.telefono.trim() || undefined,
        contrasena: form.contrasena,
        rol_id: Number(form.rol_id),
        area_id: Number(form.area_id),
      });
      setShowCreateModal(false);
      const usersData = await userService.getAll();
      setUsers(usersData);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || 'Error al crear usuario.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!form.nombre || !form.correo || !form.rol_id || !form.area_id) {
      setError('Completa todos los campos obligatorios.');
      return;
    }
    if (!editingUser) return;

    setLoading(true);
    try {
      await userService.update({
        id: editingUser.id,
        nombre: form.nombre.trim(),
        correo: form.correo.trim().toLowerCase(),
        telefono: form.telefono.trim() || undefined,
        rol_id: Number(form.rol_id),
        area_id: Number(form.area_id),
      });
      setShowEditModal(false);
      setEditingUser(null);
      const usersData = await userService.getAll();
      setUsers(usersData);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || 'Error al actualizar usuario.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingUser) return;
    setLoading(true);
    setError('');
    try {
      await userService.delete(deletingUser.id);
      setShowDeleteModal(false);
      setDeletingUser(null);
      const usersData = await userService.getAll();
      setUsers(usersData);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || 'Error al eliminar usuario.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Identificación', 'Nombre', 'Correo', 'Teléfono', 'Rol', 'Área', 'Estado'];
    const rows = filteredUsers.map((u) => [
      u.id,
      u.identificacion,
      u.nombre,
      u.correo,
      u.telefono ?? '',
      roleById[u.rol_id] ?? 'Usuario',
      areaById.get(u.area_id) ?? `Área ${u.area_id}`,
      u.activo ? 'Activo' : 'Inactivo',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.map((v) => `"${v}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `usuarios_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getRoleBadge = (rol: string) => {
    switch (rol) {
      case 'Administrador': return 'badge badge-danger';
      case 'Supervisora': return 'badge badge-warning';
      case 'Agente': return 'badge badge-primary';
      case 'Operador': return 'badge badge-success';
      default: return 'badge badge-neutral';
    }
  };

  const showStart = visibleCount === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const showEnd = Math.min(currentPage * pageSize, visibleCount);

  return (
    <div>
      <div className="page-header page-header-split animate-fade-in">
        <div>
          <h1 className="page-title">Gestión de Usuarios</h1>
          <p className="page-subtitle">Administre los usuarios del sistema</p>
        </div>
        <button className="btn btn-primary" onClick={handleOpenCreate}>
          <span className="material-symbols-outlined">person_add</span>
          Nuevo Usuario
        </button>
      </div>

      {error && !showCreateModal && !showEditModal && !showDeleteModal && (
        <div style={{ marginBottom: 16, background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>error</span>
          {error}
        </div>
      )}

      <div className="card animate-fade-in">
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f2f4f7', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
            <span className="material-symbols-outlined" style={{ position: 'absolute', left: 10, top: 8, fontSize: 18, color: '#9ca3af' }}>search</span>
            <input
              className="input"
              style={{ paddingLeft: 34 }}
              placeholder="Buscar por nombre, correo o identificación..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select className="select" style={{ width: 180 }} value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">Todos los roles</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.nombre}</option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={handleExportCSV}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>file_download</span>
            Exportar CSV
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Área</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {paginatedUsers.length > 0 ? (
                paginatedUsers.map((u) => (
                  <tr key={u.id}>
                    <td><span style={{ fontFamily: 'monospace', fontSize: '12px' }}>#{u.id}</span></td>
                    <td style={{ fontWeight: '500' }}>{u.nombre}</td>
                    <td style={{ color: '#525f73' }}>{u.correo}</td>
                    <td><span className={getRoleBadge(roleById[u.rol_id] ?? 'Usuario')}>{roleById[u.rol_id] ?? 'Usuario'}</span></td>
                    <td>{areaById.get(u.area_id) ?? `Área ${u.area_id}`}</td>
                    <td>
                      <span className={`badge ${u.activo ? 'badge-success' : 'badge-neutral'}`}>
                        {u.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button className="btn btn-sm btn-ghost" onClick={() => handleOpenEdit(u)} title="Editar">
                          <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#1e64c8' }}>edit</span>
                        </button>
                        <button
                          className="btn btn-sm btn-ghost"
                          onClick={() => handleOpenDelete(u)}
                          title="Eliminar"
                        >
                          <span
                            className="material-symbols-outlined"
                            style={{ fontSize: '16px', color: '#dc2626' }}
                          >
                            delete
                          </span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>No hay usuarios para mostrar.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f2f4f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontSize: '13px', color: '#525f73' }}>
            Mostrando {showStart} - {showEnd} de {visibleCount} usuarios
          </p>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              className="btn btn-sm btn-secondary"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </button>
            <button
              className="btn btn-sm btn-secondary"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>

      {/* ── Modal: Crear Usuario ── */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h3>Crear nuevo usuario</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowCreateModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {error && (
                  <div style={{ marginBottom: 16, background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>error</span>
                    {error}
                  </div>
                )}
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Identificación *
                    </label>
                    <input className="input" value={form.identificacion} onChange={e => setForm(f => ({ ...f, identificacion: e.target.value }))} placeholder="1000123456" />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Nombre completo *
                    </label>
                    <input className="input" value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Juan Perez" />
                  </div>
                </div>
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Correo *
                    </label>
                    <input type="email" className="input" value={form.correo} onChange={e => setForm(f => ({ ...f, correo: e.target.value }))} placeholder="correo@ejemplo.com" />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Teléfono
                    </label>
                    <input className="input" value={form.telefono} onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))} placeholder="3001234567" />
                  </div>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                    Contraseña *
                  </label>
                  <input type="password" className="input" value={form.contrasena} onChange={e => setForm(f => ({ ...f, contrasena: e.target.value }))} placeholder="Mínimo 8 caracteres" />
                </div>
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Rol *
                    </label>
                    <select className="select" style={{ width: '100%' }} value={form.rol_id} onChange={e => setForm(f => ({ ...f, rol_id: e.target.value }))}>
                      <option value="">Seleccionar rol...</option>
                      {roles.map(r => (
                        <option key={r.id} value={r.id}>{r.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Área *
                    </label>
                    <select className="select" style={{ width: '100%' }} value={form.area_id} onChange={e => setForm(f => ({ ...f, area_id: e.target.value }))}>
                      <option value="">Seleccionar área...</option>
                      {areas.map(a => (
                        <option key={a.id} value={a.id}>{a.nombre}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Creando...' : 'Crear usuario'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Editar Usuario ── */}
      {showEditModal && editingUser && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h3>Editar usuario #{editingUser.id}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowEditModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <form onSubmit={handleEdit}>
              <div className="modal-body">
                {error && (
                  <div style={{ marginBottom: 16, background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>error</span>
                    {error}
                  </div>
                )}
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Identificación
                    </label>
                    <input className="input" value={form.identificacion} disabled style={{ background: '#f3f4f6', cursor: 'not-allowed' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Nombre completo *
                    </label>
                    <input className="input" value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Juan Perez" />
                  </div>
                </div>
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Correo *
                    </label>
                    <input type="email" className="input" value={form.correo} onChange={e => setForm(f => ({ ...f, correo: e.target.value }))} placeholder="correo@ejemplo.com" />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Teléfono
                    </label>
                    <input className="input" value={form.telefono} onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))} placeholder="3001234567" />
                  </div>
                </div>
                <div className="modal-grid-two" style={{ marginBottom: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Rol *
                    </label>
                    <select className="select" style={{ width: '100%' }} value={form.rol_id} onChange={e => setForm(f => ({ ...f, rol_id: e.target.value }))}>
                      <option value="">Seleccionar rol...</option>
                      {roles.map(r => (
                        <option key={r.id} value={r.id}>{r.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: '#525f73', marginBottom: 6 }}>
                      Área *
                    </label>
                    <select className="select" style={{ width: '100%' }} value={form.area_id} onChange={e => setForm(f => ({ ...f, area_id: e.target.value }))}>
                      <option value="">Seleccionar área...</option>
                      {areas.map(a => (
                        <option key={a.id} value={a.id}>{a.nombre}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Guardando...' : 'Guardar cambios'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Confirmar Eliminación ── */}
      {showDeleteModal && deletingUser && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '440px' }}>
            <div className="modal-header">
              <h3>Eliminar usuario</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowDeleteModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body">
              {error && (
                <div style={{ marginBottom: 16, background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>error</span>
                  {error}
                </div>
              )}
              <div style={{
                background: '#fef2f2',
                borderRadius: 12,
                padding: 20,
                display: 'flex',
                gap: 16,
                alignItems: 'flex-start',
                marginBottom: 8
              }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 10,
                  background: '#fee2e2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 24, color: '#dc2626' }}>warning</span>
                </div>
                <div>
                  <p style={{ fontWeight: 600, color: '#991b1b', marginBottom: 6, fontSize: 14 }}>
                    ¿Estás seguro de que deseas eliminar este usuario?
                  </p>
                  <p style={{ fontSize: 13, color: '#7f1d1d', lineHeight: 1.5 }}>
                    Se eliminará permanentemente a <strong>{deletingUser.nombre}</strong> ({deletingUser.correo}).
                    Esta acción no se puede deshacer.
                  </p>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setShowDeleteModal(false)}>
                Cancelar
              </button>
              <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={loading}>
                {loading ? (
                  <>
                    <span className="material-symbols-outlined animate-spin" style={{ fontSize: 16 }}>progress_activity</span>
                    Eliminando...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>delete</span>
                    Eliminar usuario
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
