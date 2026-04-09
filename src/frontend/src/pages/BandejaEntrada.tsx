import { useEffect, useMemo, useState } from 'react';
import { pqrService } from '../services/pqrService';
import { catalogService } from '../services/catalogService';
import { useAuthStore } from '../stores/authStore';
import type { Classification, PQR } from '../types';

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

function getConfidencePercent(confidence: number) {
  if (confidence <= 1) {
    return Math.round(confidence * 100);
  }
  return Math.round(confidence);
}

export function BandejaEntrada() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'pendientes' | 'validados'>('pendientes');
  const [filtroPrioridad, setFiltroPrioridad] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedPQR, setSelectedPQR] = useState<PQR | null>(null);
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [prioridades, setPrioridades] = useState<string[]>([]);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [classificationByPqr, setClassificationByPqr] = useState<Record<number, Classification | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');

  const canValidate = ['admin', 'supervisor', 'agente'].includes(user?.rol_id || '');

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      setLoading(true);
      setError('');

      try {
        const [pqrData, categoriesData, prioritiesData] = await Promise.all([
          pqrService.getAll(),
          catalogService.getCategories(),
          catalogService.getPriorities(),
        ]);

        if (!isMounted) {
          return;
        }

        setPqrs(pqrData);

        const apiCategories = categoriesData.map((item) => item.nombre).filter(Boolean);
        const apiPriorities = prioritiesData.map((item) => item.nombre).filter(Boolean);

        const dbCategories = Array.from(new Set(pqrData.map((item) => item.categoria).filter(Boolean))) as string[];
        const dbPriorities = Array.from(new Set(pqrData.map((item) => item.prioridad).filter(Boolean))) as string[];

        setCategorias(apiCategories.length > 0 ? apiCategories : dbCategories);
        setPrioridades(apiPriorities.length > 0 ? apiPriorities : dbPriorities);

        const classificationPairs = await Promise.all(
          pqrData
            .filter((item) => !['resuelta', 'cerrada'].includes(item.estado.toLowerCase()))
            .map(async (item) => {
              try {
                const classification = await pqrService.getClassification(item.id);
                return [item.id, classification] as const;
              } catch {
                return [item.id, null] as const;
              }
            })
        );

        if (!isMounted) {
          return;
        }

        const map: Record<number, Classification | null> = {};
        classificationPairs.forEach(([id, classification]) => {
          map[id] = classification;
        });
        setClassificationByPqr(map);
      } catch {
        if (isMounted) {
          setError('No fue posible cargar las PQR desde la API.');
          setPqrs([]);
          setClassificationByPqr({});
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredPQRS = useMemo(() => {
    return pqrs.filter((pqr) => {
      const status = pqr.estado.toLowerCase();
      const isPending = !['resuelta', 'cerrada'].includes(status);

      if (activeTab === 'pendientes' && !isPending) {
        return false;
      }
      if (activeTab === 'validados' && isPending) {
        return false;
      }

      if (filtroPrioridad && (pqr.prioridad || '').toLowerCase() !== filtroPrioridad.toLowerCase()) {
        return false;
      }

      if (filtroCategoria && (pqr.categoria || '').toLowerCase() !== filtroCategoria.toLowerCase()) {
        return false;
      }

      const search = searchText.trim().toLowerCase();
      if (search) {
        const text = `${pqr.id} ${pqr.titulo} ${pqr.descripcion} ${pqr.usuario_nombre || ''}`.toLowerCase();
        if (!text.includes(search)) {
          return false;
        }
      }

      return true;
    });
  }, [activeTab, filtroCategoria, filtroPrioridad, pqrs, searchText]);

  const pendientesCount = useMemo(() => pqrs.filter((p) => !['resuelta', 'cerrada'].includes(p.estado.toLowerCase())).length, [pqrs]);

  const avgConfidence = useMemo(() => {
    const values = Object.values(classificationByPqr).filter((item): item is Classification => item !== null);
    if (!values.length) {
      return null;
    }

    const total = values.reduce((acc, item) => acc + getConfidencePercent(item.confianza), 0);
    return Math.round(total / values.length);
  }, [classificationByPqr]);

  const getBadgeClass = (estado: string) => {
    switch (estado.toLowerCase()) {
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

  const openDetail = (pqr: PQR) => {
    setSelectedPQR(pqr);
    setShowModal(true);
  };

  const handleValidate = async (pqr: PQR) => {
    const classification = classificationByPqr[pqr.id];
    if (!classification) {
      return;
    }

    try {
      await pqrService.validateClassification({
        id: Number(classification.id),
        pqr_id: Number(classification.pqr_id),
        modelo_version: classification.modelo_version,
        categoria_id: Number(classification.categoria_id),
        prioridad_id: Number(classification.prioridad_id),
        confianza: classification.confianza,
        origen: classification.origen,
        fue_corregida: true,
        validado_por: user?.id ? Number(user.id) : undefined,
        created_at: classification.created_at,
      });

      const updated = await pqrService.getClassification(pqr.id);
      setClassificationByPqr((prev) => ({ ...prev, [pqr.id]: updated }));
    } catch {
      setError('No fue posible validar la clasificación seleccionada.');
    }
  };

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Bandeja de Entrada</h1>
        <p className="page-subtitle">Supervisión y validación de clasificaciones automáticas por IA</p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', gap: '12px', flexWrap: 'wrap' }}>
        <div className="tabs">
          <button className={`tab ${activeTab === 'pendientes' ? 'active' : ''}`} onClick={() => setActiveTab('pendientes')}>
            Pendientes ({pendientesCount})
          </button>
          <button className={`tab ${activeTab === 'validados' ? 'active' : ''}`} onClick={() => setActiveTab('validados')}>
            Validados
          </button>
        </div>
        <input
          className="input"
          style={{ width: '340px', maxWidth: '100%' }}
          placeholder="Buscar por ID, asunto o usuario..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
      </div>

      <div className="filters-grid">
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Filtrar por Prioridad</p>
          <select className="select" value={filtroPrioridad} onChange={(e) => setFiltroPrioridad(e.target.value)}>
            <option value="">Todas</option>
            {prioridades.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Filtrar por Categoria</p>
          <select className="select" value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)}>
            <option value="">Todas</option>
            {categorias.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>
        <div className="card card-static" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '4px' }}>Confianza IA</p>
            <p style={{ fontSize: '24px', fontWeight: '800' }}>{avgConfidence !== null ? `${avgConfidence}%` : 'N/D'}</p>
          </div>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', border: '4px solid #e6e8eb', borderTopColor: '#003d9b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '10px', fontWeight: '700', color: '#003d9b' }}>AVG</span>
          </div>
        </div>
        <div className="card card-static" style={{ padding: '16px', background: '#003d9b', display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#fff' }}>
          <div>
            <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', opacity: 0.8, marginBottom: '4px' }}>Total en Vista</p>
            <p style={{ fontSize: '24px', fontWeight: '800' }}>{filteredPQRS.length}</p>
          </div>
          <span className="material-symbols-outlined" style={{ opacity: 0.5, fontSize: '32px' }}>inbox</span>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '16px', background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: '10px', fontSize: '14px' }}>
          {error}
        </div>
      )}

      <div className="card animate-fade-in" style={{ opacity: 0 }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Categoria</th>
                <th>Prioridad</th>
                <th>Confianza</th>
                <th>Estado</th>
                <th style={{ textAlign: 'right' }}>Accion</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>Cargando datos...</td>
                </tr>
              ) : filteredPQRS.length > 0 ? (
                filteredPQRS.map((pqr) => {
                  const classification = classificationByPqr[pqr.id];
                  const confidence = classification ? getConfidencePercent(classification.confianza) : null;
                  return (
                    <tr key={pqr.id}>
                      <td><span style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: '600', color: '#003d9b' }}>#{pqr.id}</span></td>
                      <td><span style={{ fontSize: '13px', color: '#525f73' }}>{formatDateLabel(pqr.created_at || pqr.updated_at)}</span></td>
                      <td>
                        <p style={{ fontWeight: '500', marginBottom: '4px' }}>{pqr.titulo}</p>
                        <p style={{ fontSize: '12px', color: '#94a3b8' }}>Usuario: {pqr.usuario_nombre || pqr.usuario_id || '-'}</p>
                      </td>
                      <td><span className="badge badge-neutral">{pqr.categoria || 'N/D'}</span></td>
                      <td><span className={getPriorityBadge(pqr.prioridad || 'media')}>{pqr.prioridad || 'N/D'}</span></td>
                      <td>
                        {confidence !== null ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div className="progress-bar" style={{ width: '60px' }}>
                              <div className="progress-fill" style={{ width: `${confidence}%`, background: confidence > 90 ? '#047857' : '#003d9b' }}></div>
                            </div>
                            <span style={{ fontSize: '12px', fontWeight: '600', color: '#003d9b' }}>{confidence}%</span>
                          </div>
                        ) : (
                          <span style={{ fontSize: '12px', color: '#64748b' }}>N/D</span>
                        )}
                      </td>
                      <td><span className={getBadgeClass(pqr.estado)}>{pqr.estado.replace('_', ' ')}</span></td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '8px' }}>
                          {activeTab === 'pendientes' && canValidate && classification ? (
                            <button className="btn btn-sm btn-primary" onClick={() => handleValidate(pqr)}>Validar</button>
                          ) : null}
                          <button className="btn btn-sm btn-secondary" onClick={() => openDetail(pqr)}>Ver</button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>No hay solicitudes para los filtros actuales.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f2f4f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontSize: '13px', color: '#525f73' }}>
            Mostrando <strong>{filteredPQRS.length}</strong> de {pqrs.length} solicitudes
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-sm btn-secondary" disabled>Anterior</button>
            <button className="btn btn-sm btn-secondary" disabled>Siguiente</button>
          </div>
        </div>
      </div>

      {showModal && selectedPQR && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Detalle de PQR</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="modal-grid-two">
                <div>
                  <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>ID</p>
                  <p style={{ fontWeight: '600', fontFamily: 'monospace' }}>#{selectedPQR.id}</p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Tipo</p>
                  <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{selectedPQR.tipo}</span>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Categoria</p>
                  <span className="badge badge-primary">{selectedPQR.categoria || 'N/D'}</span>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Prioridad</p>
                  <span className={getPriorityBadge(selectedPQR.prioridad || 'media')}>{selectedPQR.prioridad || 'N/D'}</span>
                </div>
              </div>
              <div>
                <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Descripción</p>
                <p style={{ padding: '12px', background: '#f8fafc', borderRadius: '10px', fontSize: '14px' }}>{selectedPQR.descripcion}</p>
              </div>
              <div>
                <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Estado actual</p>
                <span className={getBadgeClass(selectedPQR.estado)}>{selectedPQR.estado.replace('_', ' ')}</span>
              </div>
              {classificationByPqr[selectedPQR.id] && (
                <div>
                  <p style={{ fontSize: '11px', color: '#525f73', marginBottom: '4px' }}>Clasificacion IA</p>
                  <p style={{ fontSize: '14px', color: '#334155' }}>
                    Modelo {classificationByPqr[selectedPQR.id]?.modelo_version} | Confianza {getConfidencePercent(classificationByPqr[selectedPQR.id]?.confianza || 0)}%
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
