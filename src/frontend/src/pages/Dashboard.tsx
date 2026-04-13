import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { reportService } from '../services/reportService';
import { pqrService } from '../services/pqrService';
import type { PQR } from '../types';

const chartColors = ['#1e64c8', '#0f766e', '#c87a1e', '#475569', '#be123c'];

function formatDateLabel(value?: string) {
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
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function Dashboard() {
  const { user } = useAuthStore();
  const [dashboardStats, setDashboardStats] = useState({
    total: 0,
    pendientes: 0,
    resueltas: 0,
    enProceso: 0,
  });
  const [categoryStats, setCategoryStats] = useState<Array<{ name: string; count: number; color: string }>>([]);
  const [recentPQRS, setRecentPQRS] = useState<PQR[]>([]);
  const [avgConfidence, setAvgConfidence] = useState<number | null>(null);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const loadDashboardData = async () => {
      try {
        const [dashboard, byCategory, pqrs] = await Promise.all([
          reportService.getDashboard(),
          reportService.getByCategory(),
          pqrService.getAll(),
        ]);

        if (!isMounted) {
          return;
        }

        const total = dashboard.total;
        setLoadError('');
        setDashboardStats({
          total,
          pendientes: dashboard.pendientes,
          resueltas: dashboard.resueltas,
          enProceso: Math.max(total - dashboard.pendientes - dashboard.resueltas, 0),
        });

        setCategoryStats(
          byCategory.map((item, index) => ({
            name: item.categoria,
            count: item.cantidad,
            color: chartColors[index % chartColors.length],
          }))
        );

        const sortedRecent = [...pqrs]
          .sort((a, b) => b.id - a.id)
          .slice(0, 5);
        setRecentPQRS(sortedRecent);

        try {
          const classifications = await pqrService.getAllClassifications();
          if (classifications.length > 0) {
            const avg = classifications.reduce((acc, item) => acc + item.confianza, 0) / classifications.length;
            setAvgConfidence(Math.round(avg * 100));
          } else {
            setAvgConfidence(null);
          }
        } catch {
          setAvgConfidence(null);
        }
      } catch {
        if (isMounted) {
          setLoadError('No fue posible cargar los indicadores del dashboard. Verifica conexión y permisos.');
          setCategoryStats([]);
          setRecentPQRS([]);
          setDashboardStats({ total: 0, pendientes: 0, resueltas: 0, enProceso: 0 });
          setAvgConfidence(null);
        }
      }
    };

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  const resolutionRate = useMemo(() => {
    if (!dashboardStats.total) {
      return 0;
    }
    return Math.round((dashboardStats.resueltas / dashboardStats.total) * 100);
  }, [dashboardStats]);

  const pendingRate = useMemo(() => {
    if (!dashboardStats.total) {
      return 0;
    }
    return Math.round((dashboardStats.pendientes / dashboardStats.total) * 100);
  }, [dashboardStats]);

  const statsCards = [
    { label: 'Total PQRs', value: dashboardStats.total, icon: 'inbox', color: '#003d9b' },
    { label: 'Pendientes', value: dashboardStats.pendientes, icon: 'pending_actions', color: '#d97706' },
    { label: 'Resueltas', value: dashboardStats.resueltas, icon: 'check_circle', color: '#047857' },
    { label: 'En Proceso', value: dashboardStats.enProceso, icon: 'hourglass_top', color: '#525f73' },
  ];

  const getRoleGreeting = () => {
    switch (user?.rol_id) {
      case 'admin':
        return 'Panel de Administración';
      case 'supervisor':
      case 'operador':
        return 'Panel de Supervisión';
      case 'agente':
        return 'Panel del Agente';
      default:
        return 'Bienvenido';
    }
  };

  const getRoleActions = () => {
    switch (user?.rol_id) {
      case 'admin':
        return [
          { label: 'Gestionar usuarios', icon: 'group', path: '/usuarios' },
          { label: 'Configurar IA', icon: 'psychology', path: '/gestion-ia' },
        ];
      case 'supervisor':
        return [
          { label: 'Validar Clasificaciones', icon: 'fact_check', path: '/bandeja-entrada' },
          { label: 'Ver Reportes', icon: 'analytics', path: '/reportes' },
        ];
      case 'operador':
        return [
          { label: 'Validar Clasificaciones', icon: 'fact_check', path: '/bandeja-entrada' },
          { label: 'Gestión de PQRs', icon: 'assignment', path: '/gestion-pqrs' },
        ];
      case 'agente':
        return [{ label: 'Atender PQRs', icon: 'inbox', path: '/bandeja-entrada' }];
      default:
        return [];
    }
  };

  const getBadgeClass = (estado: string) => {
    switch (estado) {
      case 'pendiente':
      case 'registrada':
        return 'badge badge-warning';
      case 'resuelta':
      case 'cerrada':
        return 'badge badge-success';
      case 'en_proceso':
        return 'badge badge-primary';
      default:
        return 'badge badge-neutral';
    }
  };

  const getPriorityBadge = (prioridad: string) => {
    switch (prioridad.toLowerCase()) {
      case 'urgente':
        return 'badge badge-danger';
      case 'alta':
        return 'badge badge-warning';
      case 'media':
        return 'badge badge-neutral';
      default:
        return 'badge badge-neutral';
    }
  };

  const maxCategoryCount = Math.max(...categoryStats.map((cat) => cat.count), 1);

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">{getRoleGreeting()}</h1>
        <p className="page-subtitle">
          Resumen del sistema - {new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      <div className="card" style={{ marginBottom: '18px', padding: '14px 18px', background: 'linear-gradient(90deg, #ecf4ff 0%, #f7fbff 100%)' }}>
        <p style={{ fontSize: '13px', fontWeight: 600, color: '#1553a1' }}>
          Panel ejecutivo: indicadores operativos, calidad de clasificación IA y estado de atención.
        </p>
      </div>

      {loadError ? (
        <div className="card" style={{ marginBottom: '16px', padding: '14px 18px', borderLeft: '4px solid #dc2626', background: '#fff5f5' }}>
          <p style={{ fontSize: '13px', fontWeight: 600, color: '#991b1b' }}>{loadError}</p>
        </div>
      ) : null}

      <div className="dashboard-stats-grid">
        {statsCards.map((stat, i) => (
          <div key={stat.label} className={`stat-card animate-fade-in stagger-${i + 1}`} style={{ opacity: 0, background: 'linear-gradient(180deg, #ffffff 0%, #f9fbff 100%)' }}>
            <div className="stat-icon" style={{ background: stat.color }}>
              <span className="material-symbols-outlined">{stat.icon}</span>
            </div>
            <div className="stat-value">{stat.value.toLocaleString()}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="dashboard-main-grid">
        <div className="card animate-fade-in" style={{ opacity: 0, animationDelay: '0.2s', borderTop: '4px solid #1e64c8' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '700' }}>PQRs Recientes</h2>
            <Link to="/bandeja-entrada" className="btn btn-sm btn-secondary">Ver todas</Link>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Descripción</th>
                  <th>Tipo</th>
                  <th>Prioridad</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {recentPQRS.length > 0 ? (
                  recentPQRS.map((pqr) => (
                    <tr key={pqr.id}>
                      <td><span style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: '600', color: '#003d9b' }}>#{pqr.id}</span></td>
                      <td>
                        <p style={{ fontWeight: '500', marginBottom: '4px' }}>{pqr.titulo}</p>
                        <p style={{ fontSize: '12px', color: '#94a3b8' }}>{formatDateLabel(pqr.created_at || pqr.updated_at)}</p>
                      </td>
                      <td><span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{pqr.tipo}</span></td>
                      <td><span className={getPriorityBadge(pqr.prioridad || 'media')}>{pqr.prioridad || 'N/D'}</span></td>
                      <td><span className={getBadgeClass(pqr.estado)}>{pqr.estado.replace('_', ' ')}</span></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>No hay PQR registradas.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card animate-fade-in" style={{ opacity: 0, animationDelay: '0.3s', borderTop: '4px solid #0f766e' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Por Categoria</h2>
          </div>
          <div style={{ padding: '20px 24px' }}>
            {categoryStats.length > 0 ? (
              categoryStats.map((cat) => (
                <div key={cat.name} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: '500' }}>{cat.name}</span>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: '#003d9b' }}>{cat.count}</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${(cat.count / maxCategoryCount) * 100}%`, background: cat.color }}></div>
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#64748b', fontSize: '13px' }}>No hay datos de categorias disponibles.</p>
            )}
          </div>
        </div>
      </div>

      {getRoleActions().length > 0 && (
        <div className="card animate-fade-in" style={{ marginTop: '24px', opacity: 0, animationDelay: '0.4s' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Acciones rápidas</h2>
          </div>
          <div style={{ padding: '20px 24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {getRoleActions().map((action) => (
              <Link key={action.label} to={action.path} className="btn btn-primary">
                <span className="material-symbols-outlined">{action.icon}</span>
                {action.label}
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="card animate-fade-in" style={{ marginTop: '24px', opacity: 0, animationDelay: '0.5s' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Métricas del sistema</h2>
        </div>
        <div className="metrics-grid" style={{ padding: '24px' }}>
          <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
            <div style={{ fontSize: '36px', fontWeight: '800', color: '#003d9b' }}>
              {avgConfidence !== null ? `${avgConfidence}%` : 'N/D'}
            </div>
            <p style={{ fontSize: '13px', color: '#525f73', marginTop: '8px' }}>Confianza promedio IA</p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
            <div style={{ fontSize: '36px', fontWeight: '800', color: '#047857' }}>{resolutionRate}%</div>
            <p style={{ fontSize: '13px', color: '#525f73', marginTop: '8px' }}>Tasa de resolucion</p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
            <div style={{ fontSize: '36px', fontWeight: '800', color: '#525f73' }}>{pendingRate}%</div>
            <p style={{ fontSize: '13px', color: '#525f73', marginTop: '8px' }}>Pendientes sobre total</p>
          </div>
        </div>
      </div>
    </div>
  );
}
