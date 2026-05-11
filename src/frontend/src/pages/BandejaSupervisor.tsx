import { useEffect, useMemo, useRef, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { pqrService } from '../services/pqrService';
import { catalogService } from '../services/catalogService';
import { userService, type UserListItem } from '../services/userService';
import { fileService } from '../services/fileService';
import { ModalVisualizador } from '../components/visualizador/ModalVisualizador';
import type { PQR, PQRFile, Classification } from '../types';

interface HistoryEntry {
  id: number;
  pqr_id: number;
  usuario_id: number | null;
  accion: string;
  detalle: string | null;
  created_at: string;
}

function formatDate(value?: string) {
  if (!value) return '-';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleDateString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

function getEstadoBadge(estado: string) {
  const map: Record<string, string> = { pendiente: 'warning', en_proceso: 'info', resuelta: 'success', cerrada: 'neutral' };
  return map[estado.toLowerCase()] || 'neutral';
}

const estadoVisual: Record<string, { color: string; bg: string }> = {
  pendiente: { color: '#9a5b00', bg: '#fff4db' },
  en_proceso: { color: '#1553a1', bg: '#eaf2ff' },
  resuelta: { color: '#166534', bg: '#e8f9ef' },
  cerrada: { color: '#475569', bg: '#f1f5f9' },
};

function confPct(v: number) { return v <= 1 ? Math.round(v * 100) : Math.round(v); }

export function BandejaSupervisor() {
  const { user } = useAuthStore();

  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroValidacion, setFiltroValidacion] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [filtroPrioridad, setFiltroPrioridad] = useState('');
  const [activeTab, setActiveTab] = useState<'pendientes' | 'proceso' | 'resueltas'>('pendientes');
  const [feedback, setFeedback] = useState('');

  const [selectedPqr, setSelectedPqr] = useState<PQR | null>(null);
  const [showModal, setShowModal] = useState(false);

  const [classifications, setClassifications] = useState<Record<number, Classification | null>>({});
  const [history, setHistory] = useState<History[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [attachments, setAttachments] = useState<PQRFile[]>([]);
  const [loadingAttachments, setLoadingAttachments] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);

  const [categoriasData, setCategoriasData] = useState<{ id: number; nombre: string }[]>([]);
  const [prioridadesData, setPrioridadesData] = useState<{ id: number; nombre: string }[]>([]);
  const [supervisors, setSupervisors] = useState<UserListItem[]>([]);
  const [asignarSupervisorId, setAsignarSupervisorId] = useState('');

  const [clasificarCategoria, setClasificarCategoria] = useState('');
  const [clasificarPrioridad, setClasificarPrioridad] = useState('');
  const [clasificarComentario, setClasificarComentario] = useState('');
  const [resolverRespuesta, setResolverRespuesta] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [drawerCategoria, setDrawerCategoria] = useState('');
  const [drawerPrioridad, setDrawerPrioridad] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true); setError('');
      try {
        const params = user?.rol_id === 'admin' ? {} : { supervisor_id: Number(user?.id) };
        const [pqrData, cats, pris, sups] = await Promise.all([
          pqrService.getAll(params),
          catalogService.getCategories(),
          catalogService.getPriorities(),
          userService.getSupervisors(),
        ]);
        if (!mounted) return;
        setPqrs(pqrData);
        setCategoriasData(cats.map(c => ({ id: Number(c.id), nombre: c.nombre })));
        setPrioridadesData(pris.map(p => ({ id: Number(p.id), nombre: p.nombre })));
        setSupervisors(sups);

        const clsMap: Record<number, Classification | null> = {};
        await Promise.all(pqrData.map(async (pqr) => {
          try { clsMap[pqr.id] = await pqrService.getClassification(pqr.id); }
          catch { clsMap[pqr.id] = null; }
        }));
        setClassifications(clsMap);
      } catch {
        if (mounted) setError('No fue posible cargar los datos.');
      } finally { if (mounted) setLoading(false); }
    };
    load();
    return () => { mounted = false; };
  }, [user]);

  const loadHistory = async (pqrId: number) => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`/api/historial/pqr/${pqrId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setHistory(data?.data || []);
    } catch { setHistory([]); }
    finally { setLoadingHistory(false); }
  };

  const loadAttachments = async (pqrId: number) => {
    setLoadingAttachments(true);
    try {
      const files = await fileService.getByPqr(pqrId);
      setAttachments(files);
    } catch { setAttachments([]); }
    finally { setLoadingAttachments(false); }
  };

  const openDetail = (pqr: PQR) => {
    setSelectedPqr(pqr);
    loadHistory(pqr.id);
    loadAttachments(pqr.id);
    const cls = classifications[pqr.id];
    setClasificarCategoria(pqr.categoria || '');
    setClasificarPrioridad(pqr.prioridad || '');
    setClasificarComentario('');
    setResolverRespuesta('');
    setDrawerCategoria(categoriasData.find(c => c.id === Number(cls?.categoria_id))?.nombre || pqr.categoria || '');
    setDrawerPrioridad(prioridadesData.find(p => p.id === Number(cls?.prioridad_id))?.nombre || pqr.prioridad || '');
    setShowModal(true);
  };

  const handleClasificar = async () => {
    if (!selectedPqr || !clasificarCategoria || !clasificarPrioridad) return;
    setActionLoading(true);
    try {
      const updated = await pqrService.clasificar(selectedPqr.id, clasificarCategoria, clasificarPrioridad, clasificarComentario || undefined);
      setPqrs(pqrs.map(p => p.id === updated.id ? updated : p));
      setSelectedPqr(updated);
      loadHistory(updated.id);
      setFeedback('PQR clasificada correctamente.');
    } catch { setFeedback('Error al clasificar la PQR.'); }
    finally { setActionLoading(false); }
  };

  const handleResolver = async () => {
    if (!selectedPqr || !resolverRespuesta.trim()) return;
    setActionLoading(true);
    try {
      const updated = await pqrService.resolver(selectedPqr.id, resolverRespuesta.trim());
      setPqrs(pqrs.map(p => p.id === updated.id ? updated : p));
      setSelectedPqr(updated);
      loadHistory(updated.id);
      setResolverRespuesta('');
      setFeedback('PQR resuelta correctamente.');
    } catch { setFeedback('Error al resolver la PQR.'); }
    finally { setActionLoading(false); }
  };

  const handleAcceptAI = async () => {
    if (!selectedPqr) return;
    const cls = classifications[selectedPqr.id];
    if (!cls) return;
    setActionLoading(true);
    try {
      await pqrService.validateClassification({
        id: Number(cls.id), pqr_id: Number(cls.pqr_id), modelo_version: cls.modelo_version,
        categoria_id: Number(cls.categoria_id), prioridad_id: Number(cls.prioridad_id),
        confianza: cls.confianza, origen: cls.origen, fue_corregida: true,
        validado_por: user?.id ? Number(user.id) : undefined, created_at: cls.created_at,
      });
      const updated = await pqrService.getClassification(selectedPqr.id);
      setClassifications(prev => ({ ...prev, [selectedPqr.id]: updated }));
      setFeedback('Clasificación IA validada.');
    } catch { setFeedback('Error al validar la clasificación.'); }
    finally { setActionLoading(false); }
  };

  const handleSaveChanges = async () => {
    if (!selectedPqr) return;
    const cls = classifications[selectedPqr.id];
    if (!cls) return;
    const newCatId = categoriasData.find(c => c.nombre === drawerCategoria)?.id;
    const newPriId = prioridadesData.find(p => p.nombre === drawerPrioridad)?.id;
    if (!newCatId || !newPriId) { setFeedback('Categoría o prioridad inválida.'); return; }
    setActionLoading(true);
    try {
      await pqrService.validateClassification({
        id: Number(cls.id), pqr_id: Number(cls.pqr_id), modelo_version: cls.modelo_version,
        categoria_id: newCatId, prioridad_id: newPriId,
        confianza: cls.confianza, origen: 'MANUAL', fue_corregida: true,
        validado_por: user?.id ? Number(user.id) : undefined, created_at: cls.created_at,
      });
      const updated = await pqrService.getClassification(selectedPqr.id);
      setClassifications(prev => ({ ...prev, [selectedPqr.id]: updated }));
      setPqrs(prev => prev.map(p => p.id === selectedPqr.id ? { ...p, categoria: drawerCategoria, prioridad: drawerPrioridad } : p));
      setClasificarCategoria(drawerCategoria);
      setClasificarPrioridad(drawerPrioridad);
      setFeedback('Cambios guardados correctamente.');
    } catch { setFeedback('Error al guardar cambios.'); }
    finally { setActionLoading(false); }
  };

  const handleUploadFile = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f || !selectedPqr) return;
    setUploading(true);
    try {
      await fileService.uploadToPqr(selectedPqr.id, f);
      loadAttachments(selectedPqr.id);
      setFeedback('Archivo subido correctamente.');
    } catch { setFeedback('Error al subir archivo.'); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleAsignar = async () => {
    if (!selectedPqr || !asignarSupervisorId) return;
    setActionLoading(true);
    try {
      const updated = await pqrService.asignar(selectedPqr.id, Number(asignarSupervisorId));
      setPqrs(pqrs.map(p => p.id === updated.id ? updated : p));
      setSelectedPqr(updated);
      loadHistory(updated.id);
      setFeedback('Supervisor asignado correctamente.');
    } catch { setFeedback('Error al asignar supervisor.'); }
    finally { setActionLoading(false); }
  };

  const filteredPqrs = pqrs.filter(p => {
    const estado = p.estado.toLowerCase();
    const search = searchText.trim().toLowerCase();
    const cls = classifications[p.id];
    const matchesSearch = !search || p.titulo.toLowerCase().includes(search) || p.descripcion.toLowerCase().includes(search) || String(p.id).includes(search);
    if (!matchesSearch) return false;
    if (activeTab === 'pendientes' && estado !== 'pendiente') return false;
    if (activeTab === 'proceso' && estado !== 'en_proceso') return false;
    if (activeTab === 'resueltas' && !['resuelta', 'cerrada'].includes(estado)) return false;
    if (filtroTipo && p.tipo.toLowerCase() !== filtroTipo.toLowerCase()) return false;
    if (filtroValidacion === 'validados' && cls?.fue_corregida !== true) return false;
    if (filtroValidacion === 'pendientes' && cls?.fue_corregida === true) return false;
    if (filtroCategoria && (p.categoria || '').toLowerCase() !== filtroCategoria.toLowerCase()) return false;
    if (filtroPrioridad && (p.prioridad || '').toLowerCase() !== filtroPrioridad.toLowerCase()) return false;
    return true;
  });

  const pendientesCount = pqrs.filter(p => p.estado.toLowerCase() === 'pendiente').length;
  const procesoCount = pqrs.filter(p => p.estado.toLowerCase() === 'en_proceso').length;
  const resueltasCount = pqrs.filter(p => ['resuelta', 'cerrada'].includes(p.estado.toLowerCase())).length;

  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><p>Cargando...</p></div>;

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Pestaña de Gestión</h1>
        <p className="page-subtitle">{user?.rol_id === 'admin' ? 'Gestione y clasifique todas las PQRs del sistema en un solo lugar' : 'Clasifique, valide IA, adjunte archivos y resuelva PQRs asignadas en un solo lugar'}</p>
      </div>

      {error && <div style={{ marginBottom: 20, background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: 10 }}>{error}</div>}
      {feedback && <div style={{ marginBottom: 14, padding: '10px 14px', borderLeft: '4px solid #1e64c8', background: '#f0f7ff', borderRadius: 8, fontSize: 13, fontWeight: 600 }}>{feedback}</div>}

      <div className="tabs" style={{ marginBottom: 20 }}>
        <button className={`tab ${activeTab === 'pendientes' ? 'active' : ''}`} onClick={() => setActiveTab('pendientes')}>Pendientes ({pendientesCount})</button>
        <button className={`tab ${activeTab === 'proceso' ? 'active' : ''}`} onClick={() => setActiveTab('proceso')}>En Proceso ({procesoCount})</button>
        <button className={`tab ${activeTab === 'resueltas' ? 'active' : ''}`} onClick={() => setActiveTab('resueltas')}>Resueltas ({resueltasCount})</button>
      </div>

      <div className="card" style={{ marginBottom: 20, padding: 16 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <label style={{ fontSize: 14, fontWeight: 600 }}>Buscar:</label>
          <input className="input" style={{ width: 300 }} placeholder="Buscar por titulo, descripcion o ID..." value={searchText} onChange={e => setSearchText(e.target.value)} />
          <span style={{ fontSize: 13, color: '#6b7280' }}>({filteredPqrs.length} PQRs)</span>
        </div>
      </div>

      <div className="filters-grid">
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>
            Filtrar por Tipo
          </p>
          <select className="select" value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)}>
            <option value="">Todos</option>
            <option value="peticion">Petición</option>
            <option value="queja">Queja</option>
            <option value="reclamo">Reclamo</option>
          </select>
        </div>
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>
            Filtrar por Validación
          </p>
          <select className="select" value={filtroValidacion} onChange={e => setFiltroValidacion(e.target.value)}>
            <option value="">Todos</option>
            <option value="pendientes">Pendientes</option>
            <option value="validados">Validados</option>
          </select>
        </div>
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>
            Filtrar por Categoría
          </p>
          <select className="select" value={filtroCategoria} onChange={e => setFiltroCategoria(e.target.value)}>
            <option value="">Todas</option>
            {categoriasData.map(c => (
              <option key={c.id} value={c.nombre}>{c.nombre}</option>
            ))}
          </select>
        </div>
        <div className="card card-static" style={{ padding: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>
            Filtrar por Prioridad
          </p>
          <select className="select" value={filtroPrioridad} onChange={e => setFiltroPrioridad(e.target.value)}>
            <option value="">Todas</option>
            {prioridadesData.map(p => (
              <option key={p.id} value={p.nombre}>{p.nombre}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredPqrs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 48, color: '#9ca3af' }}>inbox</span>
          <p style={{ marginTop: 16, color: '#6b7280' }}>No hay PQRs asignadas en esta categoria.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Titulo</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th>Prioridad</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredPqrs.map(pqr => {
                const cls = classifications[pqr.id];
                const conf = cls ? confPct(cls.confianza) : null;
                return (
                  <tr key={pqr.id}>
                    <td style={{ fontFamily: 'monospace' }}>#{pqr.id}</td>
                    <td style={{ fontSize: 13 }}>{formatDate(pqr.created_at)}</td>
                    <td style={{ fontWeight: 500 }}>{pqr.titulo}</td>
                    <td style={{ textTransform: 'capitalize' }}>{pqr.tipo}</td>
                    <td>{pqr.categoria || '-'}</td>
                    <td>{pqr.prioridad || '-'}</td>
                    <td>
                      <span className={`badge badge-${getEstadoBadge(pqr.estado)}`}
                        style={{ color: estadoVisual[pqr.estado]?.color || '#334155', background: estadoVisual[pqr.estado]?.bg || '#f1f5f9' }}>
                        {pqr.estado.replace('_', ' ')}
                      </span>
                      {conf !== null && <span style={{ fontSize: 11, color: '#6b7280', marginLeft: 6 }}>IA: {conf}%</span>}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => openDetail(pqr)}>
                        <span className="material-symbols-outlined">edit</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {showModal && selectedPqr && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h3>PQR #{selectedPqr.id} — {selectedPqr.titulo}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: 20 }}>

                {/* INFO BASICA */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div><p style={{ fontSize: 12, color: '#525f73' }}>Tipo</p><p style={{ textTransform: 'capitalize' }}>{selectedPqr.tipo}</p></div>
                  <div><p style={{ fontSize: 12, color: '#525f73' }}>Usuario</p><p>{selectedPqr.usuario_nombre || `#${selectedPqr.usuario_id}`}</p></div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <p style={{ fontSize: 12, color: '#525f73' }}>Descripcion</p>
                    <p style={{ background: '#f8fafc', padding: 12, borderRadius: 10 }}>{selectedPqr.descripcion}</p>
                  </div>
                  <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8 }}>
                    <span className="badge badge-primary">{selectedPqr.categoria || 'Sin categoria'}</span>
                    <span className="badge badge-warning">{selectedPqr.prioridad || 'Sin prioridad'}</span>
                    <span className={`badge badge-${getEstadoBadge(selectedPqr.estado)}`}>{selectedPqr.estado}</span>
                  </div>
                </div>

                {/* ASIGNAR A SUPERVISOR - solo Admin */}
                {user?.rol_id === 'admin' && (
                  <div style={{ background: 'linear-gradient(135deg,#fef9ee,#fff8e7)', borderRadius: 14, padding: 20, border: '2px solid #f5e6b8' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#b8860b' }}>person_add</span>
                      <h4 style={{ fontSize: 15, fontWeight: 800, color: '#7c5e00', margin: 0 }}>
                        {selectedPqr.supervisor_id ? 'Reasignar Supervisor' : 'Asignar a Supervisor'}
                      </h4>
                      {selectedPqr.supervisor_id && (
                        <span className="badge badge-success" style={{ fontSize: 10, marginLeft: 4 }}>Asignada</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <select
                        className="select"
                        style={{ flex: 1 }}
                        value={asignarSupervisorId}
                        onChange={e => setAsignarSupervisorId(e.target.value)}
                      >
                        <option value="">Seleccionar supervisor...</option>
                        {supervisors.map(s => (
                          <option key={s.id} value={s.id}>{s.nombre}</option>
                        ))}
                      </select>
                      <button
                        className="btn btn-primary"
                        onClick={handleAsignar}
                        disabled={actionLoading || !asignarSupervisorId}
                        style={{ background: '#b8860b', borderColor: '#b8860b', whiteSpace: 'nowrap' }}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check</span>
                        Asignar
                      </button>
                    </div>
                  </div>
                )}

                {/* CLASIFICACION IA */}
                {classifications[selectedPqr.id] && (() => {
                  const cls = classifications[selectedPqr.id]!;
                  const catName = categoriasData.find(c => c.id === Number(cls.categoria_id))?.nombre || 'N/D';
                  const priName = prioridadesData.find(p => p.id === Number(cls.prioridad_id))?.nombre || 'N/D';
                  return (
                    <div style={{ background: 'linear-gradient(135deg,#ecf4ff,#f4f9ff)', borderRadius: 12, padding: 16, border: '1px solid rgba(21,83,161,0.12)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#1553a1' }}>psychology</span>
                        <p style={{ fontSize: 12, fontWeight: 700, color: '#1553a1', textTransform: 'uppercase' }}>Clasificacion IA</p>
                        {cls.fue_corregida && <span className="badge badge-success" style={{ fontSize: 10 }}>Validada</span>}
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        <div><p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>Modelo</p><p style={{ fontSize: 13, fontWeight: 600 }}>{cls.modelo_version}</p></div>
                        <div><p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>Confianza</p><p style={{ fontSize: 13, fontWeight: 600, color: '#047857' }}>{confPct(cls.confianza)}%</p></div>
                        <div><p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>Categoria sugerida</p><p style={{ fontSize: 13, fontWeight: 600 }}>{catName}</p></div>
                        <div><p style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>Prioridad sugerida</p><p style={{ fontSize: 13, fontWeight: 600 }}>{priName}</p></div>
                      </div>
                      {!cls.fue_corregida && (
                        <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                          <button className="btn btn-sm btn-secondary" onClick={handleAcceptAI} disabled={actionLoading}>
                            <span className="material-symbols-outlined" style={{ fontSize: 15 }}>verified</span> Validar IA
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* EDITAR CLASIFICACION */}
                {(selectedPqr.estado === 'pendiente' || selectedPqr.estado === 'en_proceso') && (
                  <div style={{ border: '2px solid #e6e8eb', borderRadius: 14, padding: 20 }}>
                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>edit_note</span>
                      Editar clasificacion
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label style={{ fontSize: 12, fontWeight: 600, color: '#525f73', display: 'block', marginBottom: 4 }}>Categoria</label>
                        <select className="select" style={{ width: '100%' }} value={drawerCategoria} onChange={e => setDrawerCategoria(e.target.value)}>
                          <option value="">Seleccionar...</option>
                          {categoriasData.map(c => <option key={c.id} value={c.nombre}>{c.nombre}</option>)}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, fontWeight: 600, color: '#525f73', display: 'block', marginBottom: 4 }}>Prioridad</label>
                        <select className="select" style={{ width: '100%' }} value={drawerPrioridad} onChange={e => setDrawerPrioridad(e.target.value)}>
                          <option value="">Seleccionar...</option>
                          {prioridadesData.map(p => <option key={p.id} value={p.nombre}>{p.nombre}</option>)}
                        </select>
                      </div>
                    </div>
                    <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleSaveChanges} disabled={actionLoading}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>save</span> Guardar cambios clasificacion
                    </button>
                  </div>
                )}

                {/* CLASIFICAR PQR (solo si pendiente) */}
                {selectedPqr.estado === 'pendiente' && (
                  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>category</span>
                      Clasificar y poner en proceso
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label style={{ fontSize: 12, color: '#525f73' }}>Categoria</label>
                        <select className="select" style={{ width: '100%' }} value={clasificarCategoria} onChange={e => setClasificarCategoria(e.target.value)}>
                          <option value="">Seleccionar...</option>
                          {categoriasData.map(c => <option key={c.id} value={c.nombre}>{c.nombre}</option>)}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#525f73' }}>Prioridad</label>
                        <select className="select" style={{ width: '100%' }} value={clasificarPrioridad} onChange={e => setClasificarPrioridad(e.target.value)}>
                          <option value="">Seleccionar...</option>
                          {prioridadesData.map(p => <option key={p.id} value={p.nombre}>{p.nombre}</option>)}
                        </select>
                      </div>
                    </div>
                    <div style={{ marginTop: 12 }}>
                      <label style={{ fontSize: 12, color: '#525f73' }}>Comentario (opcional)</label>
                      <textarea className="input" rows={2} placeholder="Agregar comentario o mensaje para el usuario..." value={clasificarComentario} onChange={e => setClasificarComentario(e.target.value)} />
                    </div>
                    <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleClasificar} disabled={actionLoading || !clasificarCategoria || !clasificarPrioridad}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>rocket_launch</span> Clasificar y poner en proceso
                    </button>
                  </div>
                )}

                {/* RESOLVER PQR */}
                {selectedPqr.estado === 'en_proceso' && (
                  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>check_circle</span>
                      Resolver PQR
                    </h4>
                    <div>
                      <label style={{ fontSize: 12, color: '#525f73' }}>Respuesta al usuario</label>
                      <textarea className="input" rows={3} placeholder="Escriba la respuesta al usuario..." value={resolverRespuesta} onChange={e => setResolverRespuesta(e.target.value)} />
                    </div>
                    <button className="btn btn-success" style={{ marginTop: 12, backgroundColor: '#059669' }} onClick={handleResolver} disabled={actionLoading || !resolverRespuesta.trim()}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check_circle</span> Marcar como Resuelta
                    </button>
                  </div>
                )}

                {/* ARCHIVOS ADJUNTOS */}
                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>attach_file</span>
                    Archivos adjuntos
                  </h4>
                  {loadingAttachments ? <p style={{ color: '#6b7280' }}>Cargando...</p> : attachments.length === 0 ? (
                    <p style={{ color: '#6b7280', marginBottom: 12 }}>Sin archivos adjuntos.</p>
                  ) : (
                    <div style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
                      {attachments.map(file => (
                        <div key={file.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: 13, fontWeight: 600 }}>{file.nombre}</span>
                          <button className="btn btn-secondary btn-sm" onClick={() => { setCurrentFileIndex(attachments.findIndex(f => f.id === file.id)); setShowViewer(true); }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>visibility</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <input ref={fileRef} type="file" accept="image/*,.pdf" style={{ fontSize: 13 }} />
                    <button className="btn btn-sm btn-primary" onClick={handleUploadFile} disabled={uploading}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{uploading ? 'sync' : 'cloud_upload'}</span>
                      {uploading ? 'Subiendo...' : 'Subir archivo'}
                    </button>
                  </div>
                </div>

                {/* HISTORIAL */}
                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>history</span>
                    Historial
                  </h4>
                  {loadingHistory ? <p style={{ color: '#6b7280' }}>Cargando...</p> : history.length === 0 ? (
                    <p style={{ color: '#6b7280' }}>Sin historial.</p>
                  ) : (
                    <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                      {history.map(h => (
                        <div key={h.id} style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: 600, fontSize: 13 }}>{h.accion}</span>
                            <span style={{ fontSize: 11, color: '#6b7280' }}>{formatDate(h.created_at)}</span>
                          </div>
                          {h.detalle && <p style={{ fontSize: 12, color: '#525f73', marginTop: 4 }}>{h.detalle}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}

      {showViewer && attachments.length > 0 && (
        <div className="modal-overlay" onClick={() => setShowViewer(false)} style={{ zIndex: 300 }}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '1000px', width: '80%', maxHeight: '80vh', margin: 20 }}>
            <div className="modal-header" style={{ padding: 16, borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 16 }}>Vista previa: {attachments[currentFileIndex]?.nombre}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowViewer(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body" style={{ padding: 0, height: 'calc(80vh - 80px)', overflow: 'hidden' }}>
              <ModalVisualizador isOpen={showViewer} onClose={() => setShowViewer(false)} files={attachments} currentFileIndex={currentFileIndex} onFileChange={setCurrentFileIndex} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
