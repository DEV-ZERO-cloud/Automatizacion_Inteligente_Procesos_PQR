import { useEffect, useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { pqrService } from '../../services/pqrService';

function formatNotificationDate(value?: string) {
  if (!value) {
    return 'Sin fecha';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Sin fecha';
  }

  return parsed.toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function Topbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Array<{ id: number; title: string; time: string; type: string }>>([]);

  useEffect(() => {
    let isMounted = true;

    const loadNotifications = async () => {
      try {
        const pqrs = await pqrService.getAll();
        if (!isMounted) {
          return;
        }

        const pending = pqrs
          .filter((item) => !['resuelta', 'cerrada'].includes(item.estado.toLowerCase()))
          .sort((a, b) => b.id - a.id)
          .slice(0, 4)
          .map((item) => ({
            id: item.id,
            title: item.titulo,
            time: formatNotificationDate(item.created_at || item.updated_at),
            type: 'warning',
          }));

        setNotifications(pending);
      } catch {
        if (isMounted) {
          setNotifications([]);
        }
      }
    };

    loadNotifications();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = async () => {
    try { await authService.logout(); } catch {}
    logout();
    navigate('/login');
  };

  return (
    <header className="topbar">
      <div className="flex items-center gap-4">
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">search</span>
          <input
            className="input pl-10 topbar-search"
            placeholder="Buscar PQR, cliente..."
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative">
          <button 
            className="btn btn-ghost"
            onClick={() => { setShowNotifications(!showNotifications); setShowDropdown(false); }}
          >
            <span className="material-symbols-outlined">notifications</span>
            {notifications.length > 0 && <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>}
          </button>
          {showNotifications && (
            <div className="dropdown-menu" style={{ width: '320px', right: 0 }}>
              <div className="p-3 border-b border-gray-100">
                <p className="text-sm font-semibold">Notificaciones</p>
              </div>
              {notifications.length > 0 ? (
                notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-50">
                    <p className="text-sm font-medium">{n.title}</p>
                    <p className="text-xs text-gray-500">{n.time}</p>
                  </div>
                ))
              ) : (
                <div className="p-3">
                  <p className="text-xs text-gray-500">No hay notificaciones pendientes.</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="relative">
          <button 
            className="btn btn-ghost"
            onClick={() => { setShowDropdown(!showDropdown); setShowNotifications(false); }}
          >
            <div className="avatar avatar-sm">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
            <span className="material-symbols-outlined text-gray-500">expand_more</span>
          </button>
          {showDropdown && (
            <div className="dropdown-menu">
              <div className="p-3 border-b border-gray-100">
                <p className="text-sm font-semibold">{user?.full_name || user?.username}</p>
                <p className="text-xs text-gray-500">{user?.email || user?.username}</p>
              </div>
              <button className="dropdown-item" onClick={() => navigate('/ajustes')}>
                <span className="material-symbols-outlined">settings</span>
                Configuración
              </button>
              <button className="dropdown-item danger" onClick={handleLogout}>
                <span className="material-symbols-outlined">logout</span>
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
