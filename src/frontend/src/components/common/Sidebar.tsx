import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const menuItems = [
  { path: '/dashboard', icon: 'dashboard', label: 'Dashboard', roles: ['admin', 'supervisor', 'operador', 'agente'] },
  { path: '/gestion-pqrs', icon: 'assignment', label: 'Gestión de PQRs', roles: ['admin', 'supervisor', 'operador'] },
  { path: '/mis-pqrs', icon: 'folder', label: 'Mis PQRs', roles: ['usuario'] },
  { path: '/bandeja-entrada', icon: 'inbox', label: 'Validar Clasificaciones', roles: ['admin', 'supervisor', 'operador', 'agente'] },
  { path: '/reportes', icon: 'analytics', label: 'Reportes', roles: ['admin', 'supervisor', 'agente', 'gerente'] },
  { path: '/usuarios', icon: 'group', label: 'Gestión de Usuarios', roles: ['admin'] },
  { path: '/gestion-ia', icon: 'psychology', label: 'Gestión IA', roles: ['admin'] },
  { path: '/ajustes', icon: 'settings', label: 'Configuración', roles: ['admin'] },
];

export function Sidebar() {
  const location = useLocation();
  const { user } = useAuthStore();

  const filteredItems = menuItems.filter(item => {
    if (!item.roles) return true;
    return item.roles.includes(user?.rol_id || '');
  });

  return (
    <aside className="sidebar">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="stat-icon bg-primary">
            <span className="material-symbols-outlined text-white">account_balance</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Gestión PQR</h1>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Control Corporativo</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 py-4 px-3">
        {filteredItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="avatar avatar-sm">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">{user?.full_name || user?.username}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.rol_id || 'Usuario'}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
