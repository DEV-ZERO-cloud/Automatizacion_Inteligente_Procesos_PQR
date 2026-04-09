import { useEffect, useMemo, useState } from 'react';
import { reportService } from '../services/reportService';
import { pqrService } from '../services/pqrService';
import type { PQR } from '../types';

const categoryColors = ['#1e64c8', '#0f766e', '#c87a1e', '#475569', '#be123c'];
const priorityColors = ['#be123c', '#c87a1e', '#475569', '#64748b'];

function rangeToDays(range: string): number {
  switch (range) {
    case '7d':
      return 7;
    case '30d':
      return 30;
    case '90d':
      return 90;
    case '1y':
      return 365;
    default:
      return 7;
  }
}

function buildTrendData(pqrs: PQR[], days: number) {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (days - 1));

  const labels: Array<{ label: string; dateKey: string; count: number }> = [];
  for (let i = 0; i < days; i += 1) {
    const current = new Date(start);
    current.setDate(start.getDate() + i);
    const dateKey = current.toISOString().slice(0, 10);
    labels.push({
      label: current.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit' }),
      dateKey,
      count: 0,
    });
  }

  const indexByDate = new Map(labels.map((item, index) => [item.dateKey, index]));

  pqrs.forEach((pqr) => {
    const dateValue = pqr.created_at || pqr.updated_at;
    if (!dateValue) {
      return;
    }

    const parsed = new Date(dateValue);
    if (Number.isNaN(parsed.getTime())) {
      return;
    }

    const dateKey = parsed.toISOString().slice(0, 10);
    const index = indexByDate.get(dateKey);
    if (index === undefined) {
      return;
    }

    labels[index].count += 1;
  });

  return labels;
}

export function Reportes() {
  const [dateRange, setDateRange] = useState('7d');
  const [categories, setCategories] = useState<Array<{ name: string; cantidad: number; porcentaje: number; color: string }>>([]);
  const [priorities, setPriorities] = useState<Array<{ name: string; cantidad: number; porcentaje: number; color: string }>>([]);
  const [stats, setStats] = useState({ total: 0, pendientes: 0, enProceso: 0, resueltas: 0 });
  const [trends, setTrends] = useState<Array<{ label: string; dateKey: string; count: number }>>([]);

  useEffect(() => {
    let isMounted = true;

    const loadReports = async () => {
      try {
        const [dashboard, byCategory, byPriority, pqrs] = await Promise.all([
          reportService.getDashboard(),
          reportService.getByCategory(),
          reportService.getByPriority(),
          pqrService.getAll(),
        ]);

        if (!isMounted) {
          return;
        }

        const total = dashboard.total || 0;
        setStats({
          total,
          pendientes: dashboard.pendientes,
          enProceso: Math.max(total - dashboard.pendientes - dashboard.resueltas, 0),
          resueltas: dashboard.resueltas,
        });

        setCategories(
          byCategory.map((item, index) => ({
            name: item.categoria,
            cantidad: item.cantidad,
            porcentaje: total > 0 ? Math.round((item.cantidad / total) * 100) : 0,
            color: categoryColors[index % categoryColors.length],
          }))
        );

        setPriorities(
          byPriority.map((item, index) => ({
            name: item.prioridad,
            cantidad: item.cantidad,
            porcentaje: total > 0 ? Math.round((item.cantidad / total) * 100) : 0,
            color: priorityColors[index % priorityColors.length],
          }))
        );

        const trendDays = rangeToDays(dateRange);
        setTrends(buildTrendData(pqrs, trendDays));
      } catch {
        if (isMounted) {
          setStats({ total: 0, pendientes: 0, enProceso: 0, resueltas: 0 });
          setCategories([]);
          setPriorities([]);
          setTrends([]);
        }
      }
    };

    loadReports();
    return () => {
      isMounted = false;
    };
  }, [dateRange]);

  const resolvedRate = useMemo(() => {
    if (!stats.total) {
      return 0;
    }
    return Math.round((stats.resueltas / stats.total) * 100);
  }, [stats]);

  const maxTrendValue = Math.max(...trends.map((item) => item.count), 1);

  return (
    <div>
      <div className="page-header page-header-split animate-fade-in">
        <div>
          <h1 className="page-title">Reportes Estadisticos</h1>
          <p className="page-subtitle">Análisis ejecutivo del sistema PQR</p>
        </div>
        <div className="page-header-actions">
          <select className="select" value={dateRange} onChange={(e) => setDateRange(e.target.value)} style={{ width: '180px' }}>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
            <option value="90d">Últimos 90 días</option>
            <option value="1y">Último año</option>
          </select>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '16px', padding: '14px 18px', background: 'linear-gradient(90deg, #ecf4ff 0%, #f4f9ff 100%)' }}>
        <p style={{ fontSize: '13px', color: '#1553a1', fontWeight: 600 }}>
          Vista corporativa: monitoreo de volumen, distribucion y tendencia de atencion.
        </p>
      </div>

      <div className="reports-stats-grid">
        {[
          { label: 'Total', value: stats.total, icon: 'inbox', color: '#003d9b' },
          { label: 'Pendientes', value: stats.pendientes, icon: 'pending_actions', color: '#d97706' },
          { label: 'En Proceso', value: stats.enProceso, icon: 'hourglass_top', color: '#525f73' },
          { label: 'Resueltas', value: stats.resueltas, icon: 'check_circle', color: '#059669' },
          { label: 'Tasa Resueltas', value: `${resolvedRate}%`, icon: 'percent', color: '#047857' },
        ].map((stat, i) => (
          <div key={stat.label} className="stat-card" style={{ textAlign: 'center', opacity: 0, animation: `fadeIn 0.4s ease forwards ${i * 0.05}s` }}>
            <div className="stat-icon" style={{ background: stat.color, margin: '0 auto 12px' }}>
              <span className="material-symbols-outlined">{stat.icon}</span>
            </div>
            <div className="stat-value">{stat.value.toLocaleString()}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="reports-charts-grid">
        <div className="card animate-fade-in">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Distribucion por Categoria</h2>
          </div>
          <div style={{ padding: '24px' }}>
            {categories.length > 0 ? (
              categories.map((cat) => (
                <div key={cat.name} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '500' }}>{cat.name}</span>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: cat.color }}>{cat.cantidad} ({cat.porcentaje}%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${cat.porcentaje}%`, background: cat.color }}></div>
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#64748b', fontSize: '13px' }}>No hay datos de categorias para el periodo seleccionado.</p>
            )}
          </div>
        </div>

        <div className="card animate-fade-in">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Distribucion por Prioridad</h2>
          </div>
          <div style={{ padding: '24px' }}>
            {priorities.length > 0 ? (
              priorities.map((pri) => (
                <div key={pri.name} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '500' }}>{pri.name}</span>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: pri.color }}>{pri.cantidad} ({pri.porcentaje}%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${pri.porcentaje}%`, background: pri.color }}></div>
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#64748b', fontSize: '13px' }}>No hay datos de prioridades para el periodo seleccionado.</p>
            )}
          </div>
        </div>
      </div>

      <div className="card animate-fade-in">
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700' }}>Tendencias Temporales</h2>
        </div>
        <div style={{ padding: '24px' }}>
          <div className="reports-trend-grid">
            {trends.length > 0 ? (
              trends.map((item) => (
                <div key={item.dateKey}>
                  <div style={{ height: '120px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center', marginBottom: '8px' }}>
                    <div
                      style={{
                        width: '40px',
                        background: '#003d9b',
                        borderRadius: '6px 6px 0 0',
                        height: `${Math.max((item.count / maxTrendValue) * 100, item.count > 0 ? 10 : 2)}%`,
                      }}
                    ></div>
                  </div>
                  <p style={{ fontSize: '12px', fontWeight: '600', color: '#525f73' }}>{item.label}</p>
                </div>
              ))
            ) : (
              <p style={{ color: '#64748b', fontSize: '13px' }}>No hay fechas registradas en las PQR para construir una tendencia temporal.</p>
            )}
          </div>
          <p style={{ textAlign: 'center', fontSize: '13px', color: '#525f73', marginTop: '16px' }}>Volumen de PQR registradas por dia</p>
        </div>
      </div>
    </div>
  );
}
