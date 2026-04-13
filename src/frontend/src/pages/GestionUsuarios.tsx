import { useEffect, useMemo, useState } from 'react';
import { catalogService } from '../services/catalogService';
import { userService, type UserListItem } from '../services/userService';

const roleById: Record<number, string> = {
  1: 'Administrador',
  2: 'Supervisora',
  3: 'Agente',
  4: 'Usuario',
  5: 'Operador'
};

export function GestionUsuarios() {
  const [users, setUsers] = useState<Array<{ id: number; nombre: string; correo: string; rol: string; estado: string; area: string }>>([]);

  useEffect(() => {
    let isMounted = true;

    const loadUsers = async () => {
      try {
        const [usersData, areas] = await Promise.all([
          userService.getAll(),
          catalogService.getAreas(),
        ]);

        if (!isMounted) {
          return;
        }

        const areaById = new Map(areas.map((area) => [Number(area.id), area.nombre]));
        const mapped = usersData.map((user: UserListItem) => ({
          id: user.id,
          nombre: user.nombre,
          correo: user.correo,
          rol: roleById[user.rol_id] ?? 'Usuario',
          estado: 'Activo',
          area: areaById.get(user.area_id) ?? `Área ${user.area_id}`,
        }));

        setUsers(mapped);
      } catch {
        if (isMounted) {
          setUsers([]);
        }
      }
    };

    loadUsers();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalUsers = useMemo(() => users.length, [users]);

  const getRoleBadge = (rol: string) => {
    switch (rol) {
      case 'Administrador': return 'badge badge-danger';
      case 'Supervisora': return 'badge badge-warning';
      case 'Agente': return 'badge badge-primary';
      case 'Operador': return 'badge badge-success';
      default: return 'badge badge-neutral';
    }
  };

  return (
    <div>
      <div className="page-header page-header-split animate-fade-in">
        <div>
          <h1 className="page-title">Gestión de Usuarios</h1>
          <p className="page-subtitle">Administre los usuarios del sistema</p>
        </div>
        <button className="btn btn-primary">
          <span className="material-symbols-outlined">person_add</span>
          Nuevo Usuario
        </button>
      </div>

      <div className="card animate-fade-in">
        <div className="users-toolbar">
          <input className="input" placeholder="Buscar usuario..." style={{ width: '300px' }} />
          <div className="users-toolbar-actions">
            <button className="btn btn-sm btn-secondary">
              <span className="material-symbols-outlined">filter_list</span>
              Filtros
            </button>
            <button className="btn btn-sm btn-secondary">
              <span className="material-symbols-outlined">download</span>
              Exportar
            </button>
          </div>
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
              {users.length > 0 ? (
                users.map((user) => (
                  <tr key={user.id}>
                    <td><span style={{ fontFamily: 'monospace', fontSize: '12px' }}>#{user.id}</span></td>
                    <td style={{ fontWeight: '500' }}>{user.nombre}</td>
                    <td style={{ color: '#525f73' }}>{user.correo}</td>
                    <td><span className={getRoleBadge(user.rol)}>{user.rol}</span></td>
                    <td>{user.area}</td>
                    <td>
                      <span className={`badge ${user.estado === 'Activo' ? 'badge-success' : 'badge-neutral'}`}>
                        {user.estado}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-sm btn-ghost">
                          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>edit</span>
                        </button>
                        <button className="btn btn-sm btn-ghost">
                          <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#dc2626' }}>delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>
                    No hay usuarios para mostrar.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f2f4f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontSize: '13px', color: '#525f73' }}>Mostrando 1 - {totalUsers} de {totalUsers} usuarios</p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-sm btn-secondary" disabled>Anterior</button>
            <button className="btn btn-sm btn-secondary" disabled>Siguiente</button>
          </div>
        </div>
      </div>
    </div>
  );
}
