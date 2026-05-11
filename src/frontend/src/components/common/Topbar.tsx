import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { pqrService } from '../../services/pqrService';
import type { PQR } from '../../types';

function formatNotificationDate(value?: string) {
  if (!value) return 'Sin fecha';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return 'Sin fecha';
  return parsed.toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const ESTADO_BADGE: Record<string, string> = {
  registrada:  '#dae2ff|#003d9b',
  en_proceso:  '#fef3c7|#92400e',
  resuelta:    '#d1fae5|#047857',
  cerrada:     '#f2f4f7|#525f73',
  pendiente:   '#fef3c7|#92400e',
};

const TIPO_ICON: Record<string, string> = {
  peticion: 'help_outline',
  queja:    'sentiment_dissatisfied',
  reclamo:  'report_problem',
};

export function Topbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  // Dropdown states
  const [showDropdown, setShowDropdown]           = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Notifications data (re‑used for search pool)
  const [allPqrs, setAllPqrs] = useState<PQR[]>([]);
  const [notifications, setNotifications] = useState<
    Array<{ id: number; title: string; time: string; type: string }>
  >([]);

  // Search state
  const [searchQuery, setSearchQuery]   = useState('');
  const [showResults, setShowResults]   = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // ── Load PQRs once ──────────────────────────────────────────────
  useEffect(() => {
    let isMounted = true;
    pqrService.getAll().then((pqrs) => {
      if (!isMounted) return;
      setAllPqrs(pqrs);
      const pending = pqrs
        .filter((p) => !['resuelta', 'cerrada'].includes(p.estado.toLowerCase()))
        .sort((a, b) => b.id - a.id)
        .slice(0, 4)
        .map((p) => ({
          id:   p.id,
          title: p.titulo,
          time:  formatNotificationDate(p.created_at || p.updated_at),
          type:  'warning',
        }));
      setNotifications(pending);
    }).catch(() => { if (isMounted) setAllPqrs([]); });
    return () => { isMounted = false; };
  }, []);

  // ── Close search dropdown when clicking outside ──────────────────
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Filtered results (max 6) ─────────────────────────────────────
  const searchResults = (() => {
    const q = searchQuery.trim().toLowerCase();
    if (q.length < 2) return [];
    return allPqrs
      .filter((p) =>
        String(p.id).includes(q) ||
        p.titulo.toLowerCase().includes(q) ||
        (p.usuario_nombre ?? '').toLowerCase().includes(q) ||
        (p.categoria ?? '').toLowerCase().includes(q) ||
        p.tipo.toLowerCase().includes(q) ||
        p.estado.toLowerCase().includes(q)
      )
      .slice(0, 6);
  })();

  const handleLogout = async () => {
    try { await authService.logout(); } catch {}
    logout();
    navigate('/login');
  };

  const goToPqr = (id: number) => {
    setSearchQuery('');
    setShowResults(false);
    navigate(`/pqr/${id}`);
  };

  const handleSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') { setShowResults(false); setSearchQuery(''); }
    if (e.key === 'Enter' && searchResults.length === 1) goToPqr(searchResults[0].id);
  };

  // ── Agente: minimal topbar ───────────────────────────────────────
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

  // ── Estado badge colors ──────────────────────────────────────────
  const getEstadoStyle = (estado: string) => {
    const val = ESTADO_BADGE[estado.toLowerCase()] ?? '#f2f4f7|#525f73';
    const [bg, color] = val.split('|');
    return { background: bg, color, padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 700, textTransform: 'uppercase' as const, letterSpacing: '0.4px' };
  };

  return (
    <header className="topbar">
      {/* ── Left: Search ── */}
      <div className="flex items-center gap-4">
        <div className="relative" ref={searchRef}>
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            search
          </span>
          <input
            className="input pl-10 topbar-search"
            placeholder="Buscar PQR, cliente..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowResults(true);
            }}
            onFocus={() => { if (searchQuery.trim().length >= 2) setShowResults(true); }}
            onKeyDown={handleSearchKey}
            autoComplete="off"
          />

          {/* ── Results dropdown ── */}
          {showResults && searchQuery.trim().length >= 2 && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              width: 380,
              background: '#fff',
              borderRadius: 14,
              boxShadow: '0 12px 40px -8px rgba(15,23,42,0.22), 0 2px 8px rgba(15,23,42,0.06)',
              border: '1px solid rgba(15,23,42,0.08)',
              zIndex: 300,
              overflow: 'hidden',
              animation: 'fadeIn 0.15s ease',
            }}>
              {/* Header */}
              <div style={{ padding: '10px 16px', borderBottom: '1px solid #f2f4f7', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#525f73', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Resultados
                </span>
                <span style={{ fontSize: 12, color: '#94a3b8' }}>
                  {searchResults.length} encontrado{searchResults.length !== 1 ? 's' : ''}
                </span>
              </div>

              {searchResults.length > 0 ? (
                <>
                  {searchResults.map((pqr) => {
                    const icon = TIPO_ICON[pqr.tipo?.toLowerCase()] ?? 'description';
                    return (
                      <button
                        key={pqr.id}
                        onClick={() => goToPqr(pqr.id)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 12,
                          padding: '12px 16px',
                          background: 'none',
                          border: 'none',
                          borderBottom: '1px solid #f8fafc',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'background 0.15s',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
                      >
                        {/* Icon */}
                        <div style={{
                          width: 34,
                          height: 34,
                          borderRadius: 8,
                          background: '#f0f4ff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}>
                          <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#1e64c8' }}>{icon}</span>
                        </div>

                        {/* Info */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                            <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#94a3b8' }}>#{pqr.id}</span>
                            <span style={getEstadoStyle(pqr.estado)}>{pqr.estado.replace('_', ' ')}</span>
                          </div>
                          <p style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 2 }}>
                            {pqr.titulo}
                          </p>
                          {pqr.usuario_nombre && (
                            <p style={{ fontSize: 11, color: '#64748b' }}>
                              <span className="material-symbols-outlined" style={{ fontSize: 12, verticalAlign: 'middle', marginRight: 3 }}>person</span>
                              {pqr.usuario_nombre}
                            </p>
                          )}
                        </div>

                        {/* Chevron */}
                        <span className="material-symbols-outlined" style={{ fontSize: 16, color: '#c3c6d6', marginTop: 2 }}>chevron_right</span>
                      </button>
                    );
                  })}

                  {/* Footer hint */}
                  <div style={{ padding: '8px 16px', background: '#fafbff', borderTop: '1px solid #f2f4f7' }}>
                    <p style={{ fontSize: 11, color: '#94a3b8', textAlign: 'center' }}>
                      Presiona <kbd style={{ background: '#e6e8eb', borderRadius: 4, padding: '1px 5px', fontSize: 10, fontFamily: 'monospace' }}>Enter</kbd> para ir al primer resultado · <kbd style={{ background: '#e6e8eb', borderRadius: 4, padding: '1px 5px', fontSize: 10, fontFamily: 'monospace' }}>Esc</kbd> para cerrar
                    </p>
                  </div>
                </>
              ) : (
                <div style={{ padding: '24px 16px', textAlign: 'center' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 32, color: '#c3c6d6', display: 'block', marginBottom: 8 }}>search_off</span>
                  <p style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>Sin resultados para "<strong>{searchQuery}</strong>"</p>
                  <p style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>Prueba con ID, título, tipo o estado</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="badge badge-primary" style={{ textTransform: 'none' }}>Entorno productivo académico</div>
      </div>

      {/* ── Right: Notifications + User ── */}
      <div className="flex items-center gap-2">

        {/* Notifications */}
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
                  <div key={n.id} className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-50"
                    onClick={() => { setShowNotifications(false); navigate(`/pqr/${n.id}`); }}>
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

        {/* User menu */}
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
