import { useEffect, useMemo, useState } from 'react';
import { pqrService } from '../services/pqrService';
import { reportService } from '../services/reportService';
import type { Classification } from '../types';

function confidenceToPercent(value: number) {
  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

export function GestionIA() {
  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [totalPqrs, setTotalPqrs] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      setError('');
      try {
        const [classificationData, dashboard] = await Promise.all([
          pqrService.getAllClassifications(),
          reportService.getDashboard(),
        ]);

        if (!isMounted) {
          return;
        }

        setClassifications(classificationData);
        setTotalPqrs(dashboard.total);
      } catch {
        if (isMounted) {
          setClassifications([]);
          setTotalPqrs(0);
          setError('No fue posible cargar las metricas del modelo desde la API.');
        }
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const groupedVersions = useMemo(() => {
    const byVersion = new Map<string, Classification[]>();

    classifications.forEach((item) => {
      const version = item.modelo_version || 'sin_version';
      const current = byVersion.get(version) || [];
      current.push(item);
      byVersion.set(version, current);
    });

    return Array.from(byVersion.entries())
      .map(([version, items]) => {
        const avgConfidence =
          items.length > 0
            ? Math.round(items.reduce((acc, item) => acc + confidenceToPercent(item.confianza), 0) / items.length)
            : 0;
        const latest = items
          .map((item) => item.created_at)
          .filter(Boolean)
          .sort()
          .at(-1);

        return {
          version,
          registros: items.length,
          avgConfidence,
          latest: latest || 'Sin fecha',
        };
      })
      .sort((a, b) => b.registros - a.registros);
  }, [classifications]);

  const activeVersion = groupedVersions[0]?.version || 'N/D';
  const avgGlobalConfidence = useMemo(() => {
    if (!classifications.length) {
      return 0;
    }
    const total = classifications.reduce((acc, item) => acc + confidenceToPercent(item.confianza), 0);
    return Math.round(total / classifications.length);
  }, [classifications]);

  const classificationCoverage = useMemo(() => {
    if (!totalPqrs) {
      return 0;
    }
    return Math.round((classifications.length / totalPqrs) * 100);
  }, [classifications.length, totalPqrs]);

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Gestion del Modelo de IA</h1>
        <p className="page-subtitle">Indicadores de clasificacion construidos desde la base de datos</p>
      </div>

      {error && (
        <div style={{ marginBottom: '16px', background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: '10px', fontSize: '14px' }}>
          {error}
        </div>
      )}

      <div className="ia-main-grid">
        <div className="card animate-fade-in">
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Estado del Modelo</h3>
              <span className="badge badge-success">Sistema: Activo</span>
            </div>
            <div className="ia-status-grid">
              <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '8px' }}>Confianza Promedio</p>
                <p style={{ fontSize: '36px', fontWeight: '800', color: '#003d9b' }}>{avgGlobalConfidence}%</p>
              </div>
              <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '8px' }}>Cobertura de Clasificacion</p>
                <p style={{ fontSize: '20px', fontWeight: '700' }}>{classificationCoverage}%</p>
                <p style={{ fontSize: '12px', color: '#525f73' }}>{classifications.length} de {totalPqrs} PQR</p>
              </div>
              <div style={{ textAlign: 'center', padding: '20px', background: '#f8fafc', borderRadius: '12px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '8px' }}>Version Activa</p>
                <p style={{ fontSize: '20px', fontWeight: '700' }}>{activeVersion}</p>
                <span className="badge badge-primary">Produccion</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card animate-fade-in">
          <div style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Resumen Operativo</h3>
            <div style={{ display: 'grid', gap: '12px' }}>
              <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Clasificaciones Totales</p>
                <p style={{ fontWeight: '800', fontSize: '26px', color: '#003d9b' }}>{classifications.length}</p>
              </div>
              <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Versiones Detectadas</p>
                <p style={{ fontWeight: '800', fontSize: '26px', color: '#047857' }}>{groupedVersions.length}</p>
              </div>
              <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Ultima Actividad</p>
                <p style={{ fontWeight: '700' }}>{groupedVersions[0]?.latest || 'Sin registros'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card animate-fade-in">
        <div style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Historial de Versiones</h3>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th style={{ textAlign: 'right' }}>Registros</th>
                  <th style={{ textAlign: 'right' }}>Confianza Prom.</th>
                  <th>Ultimo Registro</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {groupedVersions.length > 0 ? (
                  groupedVersions.map((item, index) => (
                    <tr key={item.version}>
                      <td><span style={{ fontFamily: 'monospace', fontWeight: '600', color: '#003d9b' }}>{item.version}</span></td>
                      <td style={{ textAlign: 'right', fontWeight: '500' }}>{item.registros}</td>
                      <td style={{ textAlign: 'right', fontWeight: '700' }}>{item.avgConfidence}%</td>
                      <td>{item.latest}</td>
                      <td>
                        <span className={`badge ${index === 0 ? 'badge-success' : 'badge-neutral'}`}>
                          {index === 0 ? 'Activa' : 'Historica'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>No existen clasificaciones registradas.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
