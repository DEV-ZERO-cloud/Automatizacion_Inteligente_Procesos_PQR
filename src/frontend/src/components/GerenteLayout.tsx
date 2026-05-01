import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';

export function GerenteLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const handleLogout = async () => {
    try { await authService.logout(); } catch {}
    logout();
    navigate('/login');
  };

  const formattedDate = currentTime.toLocaleDateString('es-CO', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="gerente-shell">
      {/* ── Topbar ejecutiva ── */}
      <header className="gerente-topbar">
        {/* Marca */}
        <div className="gerente-brand">
          <div className="gerente-brand-icon">
            <span className="material-symbols-outlined">account_balance</span>
          </div>
          <div>
            <span className="gerente-brand-name">Gestión PQR</span>
            <span className="gerente-brand-sub">Panel Ejecutivo</span>
          </div>
        </div>

        {/* Centro: fecha */}
        <div className="gerente-date">
          <span className="material-symbols-outlined" style={{ fontSize: '16px', opacity: 0.7 }}>calendar_today</span>
          <span style={{ textTransform: 'capitalize' }}>{formattedDate}</span>
        </div>

        {/* Acciones */}
        <div className="gerente-topbar-actions">
          <div className="gerente-role-badge">
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>verified_user</span>
            Gerente
          </div>

          <div style={{ position: 'relative' }}>
            <button
              className="gerente-user-btn"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <div className="gerente-avatar">
                {user?.username?.charAt(0).toUpperCase() || 'G'}
              </div>
              <div className="gerente-user-info">
                <span className="gerente-user-name">{user?.full_name || user?.username}</span>
                <span className="gerente-user-email">{user?.email}</span>
              </div>
              <span className="material-symbols-outlined" style={{ fontSize: '18px', opacity: 0.7 }}>expand_more</span>
            </button>

            {showDropdown && (
              <div className="gerente-dropdown" onClick={() => setShowDropdown(false)}>
                <div className="gerente-dropdown-header">
                  <p style={{ fontWeight: 600, fontSize: '14px' }}>{user?.full_name || user?.username}</p>
                  <p style={{ fontSize: '12px', opacity: 0.7, marginTop: '2px' }}>{user?.email}</p>
                </div>
                <button className="gerente-dropdown-item danger" onClick={handleLogout}>
                  <span className="material-symbols-outlined">logout</span>
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Contenido principal ── */}
      <main className="gerente-main">
        {/* Banda de bienvenida */}
        <div className="gerente-welcome-banner animate-fade-in">
          <div className="gerente-welcome-left">
            <div className="gerente-welcome-icon">
              <span className="material-symbols-outlined">analytics</span>
            </div>
            <div>
              <h2 className="gerente-welcome-title">
                Bienvenido, {user?.full_name?.split(' ')[0] || user?.username}
              </h2>
              <p className="gerente-welcome-sub">
                Aquí tienes la vista consolidada de métricas y tendencias del sistema PQR.
              </p>
            </div>
          </div>
          <div className="gerente-welcome-right">
            <div className="gerente-kpi-pill">
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>shield_lock</span>
              Acceso de solo lectura ejecutivo
            </div>
          </div>
        </div>

        {/* Página activa (Reportes) */}
        <div className="gerente-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
