import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';

export function Topbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = async () => {
    try { await authService.logout(); } catch {}
    logout();
    navigate('/login');
  };

  if (user?.rol_id === 'agente') {
    return (
      <header className="topbar" style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 24px', background: 'transparent', borderBottom: 'none' }}>
        <button className="btn btn-ghost danger" onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444' }}>
          <span className="material-symbols-outlined">logout</span>
          Cerrar sesión
        </button>
      </header>
    );
  }

  return (
    <header className="topbar" style={{ justifyContent: 'flex-end' }}>
      <div className="relative">
        <button
          className="btn btn-ghost"
          onClick={() => setShowDropdown(!showDropdown)}
        >
          <div className="avatar avatar-sm">{user?.username?.charAt(0).toUpperCase() || 'U'}</div>
          <span className="material-symbols-outlined text-gray-500">expand_more</span>
        </button>
        {showDropdown && (
          <div className="dropdown-menu" style={{ right: 0 }}>
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
    </header>
  );
}
