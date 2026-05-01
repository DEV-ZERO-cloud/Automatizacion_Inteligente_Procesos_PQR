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
  const [drawerCategoria, setDrawerCategoria] = useState('');
  const [drawerPrioridad, setDrawerPrioridad] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);

  const canValidate = ['admin', 'supervisor', 'operador', 'agente'].includes(user?.rol_id || '');

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
    setDrawerCategoria(pqr.categoria || '');
    setDrawerPrioridad(pqr.prioridad || '');
    setShowConfirm(false);
    setShowModal(true);
  };

  const handleQuickUpdate = async (pqrId: number, field: 'categoria' | 'prioridad', value: string) => {
    try {
      await pqrService.update(pqrId, { [field]: value });
      setPqrs((prev) => prev.map(p => p.id === pqrId ? { ...p, [field]: value } : p));
    } catch {
      setError(`Error actualizando ${field} para la PQR #${pqrId}`);
    }
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
                        <td><span className={getPriorityBadge(pqr.prioridad || 'media')}>{(pqr.prioridad || 'N/D').toUpperCase()}</span></td>
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
                        <button className="btn btn-sm btn-primary" style={{ gap: '6px' }} onClick={() => openDetail(pqr)}>
                          <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>open_in_new</span>
                          Ver detalle
                        </button>
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

      {/* ── Drawer lateral ── */}
      {showModal && selectedPQR && (
        <>
          {/* Backdrop */}
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.45)', backdropFilter: 'blur(3px)', zIndex: 190 }}
            onClick={() => { setShowModal(false); setShowConfirm(false); }}
          />

          {/* Panel */}
          <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(480px, 100vw)', background: '#fff', zIndex: 200, display: 'flex', flexDirection: 'column', boxShadow: '-8px 0 40px rgba(0,0,0,0.18)', animation: 'slideInRight 0.25s ease' }}>

            {/* Header del drawer */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #f2f4f7', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(135deg,#0b3b7a,#1553a1)', color: '#fff' }}>
              <div>
                <p style={{ fontSize: '11px', opacity: 0.7, marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Detalle de solicitud</p>
                <h2 style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'Sora,sans-serif' }}>PQR #{selectedPQR.id}</h2>
              </div>
              <button onClick={() => { setShowModal(false); setShowConfirm(false); }} style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: '8px', width: '36px', height: '36px', cursor: 'pointer', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Cuerpo scrolleable */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Info básica */}
              <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                {[
                  { label: 'ID', value: `#${selectedPQR.id}`, mono: true },
                  { label: 'Tipo', value: selectedPQR.tipo },
                  { label: 'Usuario', value: selectedPQR.usuario_nombre || String(selectedPQR.usuario_id || '-') },
                  { label: 'Fecha', value: formatDateLabel(selectedPQR.created_at || selectedPQR.updated_at) },
                ].map(({ label, value, mono }) => (
                  <div key={label}>
                    <p style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px', fontWeight: 700 }}>{label}</p>
                    <p style={{ fontSize: '14px', fontWeight: 600, fontFamily: mono ? 'monospace' : undefined, color: '#0f172a', textTransform: 'capitalize' }}>{value}</p>
                  </div>
                ))}
              </div>

              {/* Título y descripción */}
              <div>
                <p style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px', fontWeight: 700 }}>Título</p>
                <p style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a', marginBottom: '12px' }}>{selectedPQR.titulo}</p>
                <p style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px', fontWeight: 700 }}>Descripción</p>
                <p style={{ fontSize: '14px', color: '#334155', lineHeight: '1.6', background: '#f8fafc', padding: '12px', borderRadius: '10px' }}>{selectedPQR.descripcion}</p>
              </div>

              {/* Estado */}
              <div>
                <p style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px', fontWeight: 700 }}>Estado</p>
                <span className={getBadgeClass(selectedPQR.estado)}>{selectedPQR.estado.replace('_', ' ')}</span>
              </div>

              {/* Clasificación IA */}
              {classificationByPqr[selectedPQR.id] && (
                <div style={{ background: 'linear-gradient(135deg,#ecf4ff,#f4f9ff)', borderRadius: '12px', padding: '14px 16px', border: '1px solid rgba(21,83,161,0.12)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#1553a1' }}>psychology</span>
                    <p style={{ fontSize: '12px', fontWeight: 700, color: '#1553a1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Clasificación IA</p>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Modelo</p>
                      <p style={{ fontSize: '13px', fontWeight: 600 }}>{classificationByPqr[selectedPQR.id]?.modelo_version || 'N/D'}</p>
                    </div>
                    <div>
                      <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Confianza</p>
                      <p style={{ fontSize: '13px', fontWeight: 600, color: '#047857' }}>{getConfidencePercent(classificationByPqr[selectedPQR.id]?.confianza || 0)}%</p>
                    </div>
                    <div>
                      <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Categoría sugerida</p>
                      <p style={{ fontSize: '13px', fontWeight: 600 }}>{classificationByPqr[selectedPQR.id]?.categoria_nombre || 'N/D'}</p>
                    </div>
                    <div>
                      <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Prioridad sugerida</p>
                      <p style={{ fontSize: '13px', fontWeight: 600 }}>{classificationByPqr[selectedPQR.id]?.prioridad_nombre || 'N/D'}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Edición de clasificación */}
              {canValidate && activeTab === 'pendientes' && (
                <div style={{ border: '2px solid #e6e8eb', borderRadius: '14px', padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#003d9b' }}>edit_note</span>
                    <p style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>Ajustar clasificación</p>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: 600, color: '#525f73', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '6px' }}>Categoría</label>
                      <select className="select" value={drawerCategoria} onChange={e => setDrawerCategoria(e.target.value)}>
                        <option value="">N/D</option>
                        {categorias.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: 600, color: '#525f73', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '6px' }}>Prioridad</label>
                      <select className="select" value={drawerPrioridad} onChange={e => setDrawerPrioridad(e.target.value)}>
                        <option value="">N/D</option>
                        {prioridades.map(pri => <option key={pri} value={pri}>{pri}</option>)}
                      </select>
                    </div>
                  </div>
                  {(drawerCategoria !== (selectedPQR.categoria || '') || drawerPrioridad !== (selectedPQR.prioridad || '')) && (
                    <div style={{ marginTop: '12px', padding: '10px 12px', background: '#fef3c7', borderRadius: '8px', border: '1px solid #fde68a', fontSize: '12px', color: '#92400e', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>info</span>
                      Tienes cambios sin guardar
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer con acciones */}
            {canValidate && activeTab === 'pendientes' && (
              <div style={{ padding: '16px 24px', borderTop: '1px solid #f2f4f7', display: 'flex', gap: '12px', background: '#fafbfc' }}>
                <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => { setShowModal(false); setShowConfirm(false); }}>
                  Cancelar
                </button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 2 }}
                  disabled={drawerCategoria === (selectedPQR.categoria || '') && drawerPrioridad === (selectedPQR.prioridad || '')}
                  onClick={() => setShowConfirm(true)}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '17px' }}>save</span>
                  Guardar cambios
                </button>
              </div>
            )}
          </div>

          {/* ── Modal de confirmación flotante ── */}
          {showConfirm && (
            <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 300 }}>
              <div style={{ background: '#fff', borderRadius: '20px', padding: '32px', maxWidth: '420px', width: '90%', boxShadow: '0 24px 64px rgba(0,0,0,0.25)', animation: 'fadeIn 0.2s ease' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                  <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: '#fef3c7', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span className="material-symbols-outlined" style={{ color: '#d97706', fontSize: '24px' }}>warning</span>
                  </div>
                  <div>
                    <h3 style={{ fontFamily: 'Sora,sans-serif', fontSize: '16px', fontWeight: 700, marginBottom: '2px' }}>Confirmar cambios</h3>
                    <p style={{ fontSize: '13px', color: '#64748b' }}>PQR #{selectedPQR.id} — {selectedPQR.titulo}</p>
                  </div>
                </div>

                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '14px', marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {drawerCategoria !== (selectedPQR.categoria || '') && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#64748b' }}>category</span>
                      <div>
                        <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Categoría</p>
                        <p style={{ fontSize: '13px' }}>
                          <span style={{ color: '#b91c1c', textDecoration: 'line-through' }}>{selectedPQR.categoria || 'N/D'}</span>
                          {' → '}
                          <span style={{ color: '#047857', fontWeight: 700 }}>{drawerCategoria}</span>
                        </p>
                      </div>
                    </div>
                  )}
                  {drawerPrioridad !== (selectedPQR.prioridad || '') && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#64748b' }}>flag</span>
                      <div>
                        <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '2px' }}>Prioridad</p>
                        <p style={{ fontSize: '13px' }}>
                          <span style={{ color: '#b91c1c', textDecoration: 'line-through' }}>{selectedPQR.prioridad || 'N/D'}</span>
                          {' → '}
                          <span style={{ color: '#047857', fontWeight: 700 }}>{drawerPrioridad}</span>
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowConfirm(false)}>
                    Volver
                  </button>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 2 }}
                    onClick={async () => {
                      const updates: Partial<{ categoria: string; prioridad: string }> = {};
                      if (drawerCategoria !== (selectedPQR.categoria || '')) updates.categoria = drawerCategoria;
                      if (drawerPrioridad !== (selectedPQR.prioridad || '')) updates.prioridad = drawerPrioridad;
                      try {
                        await pqrService.update(selectedPQR.id, updates);
                        setPqrs(prev => prev.map(p => p.id === selectedPQR.id ? { ...p, ...updates } : p));
                        setSelectedPQR({ ...selectedPQR, ...updates });
                        setShowConfirm(false);
                        setShowModal(false);
                      } catch {
                        setError('No fue posible guardar los cambios.');
                        setShowConfirm(false);
                      }
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '17px' }}>check_circle</span>
                    Confirmar y guardar
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}


