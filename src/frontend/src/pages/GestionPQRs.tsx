import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { fileService } from '../services/fileService';
import { pqrService } from '../services/pqrService';
import { userService, type UserListItem } from '../services/userService';
import { ModalVisualizador } from '../components/visualizador/ModalVisualizador';
import type { PQR, PQRFile } from '../types';

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
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getEstadoBadge(estado: string) {
  const map: Record<string, string> = {
    pendiente: 'warning',
    en_proceso: 'info',
    resuelta: 'success',
    cerrada: 'neutral'
  };
  return map[estado.toLowerCase()] || 'neutral';
}

const estadoVisual: Record<string, { color: string; bg: string }> = {
  pendiente: { color: '#9a5b00', bg: '#fff4db' },
  en_proceso: { color: '#1553a1', bg: '#eaf2ff' },
  resuelta: { color: '#166534', bg: '#e8f9ef' },
  cerrada: { color: '#475569', bg: '#f1f5f9' },
};

export function GestionPQRs() {
  const { user } = useAuthStore();
  const isAdmin = user?.rol_id === 'admin';
  const isSupervisor = user?.rol_id === 'supervisor' || user?.rol_id === 'operador';
  
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [supervisors, setSupervisors] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [selectedPqr, setSelectedPqr] = useState<PQR | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [attachments, setAttachments] = useState<PQRFile[]>([]);
  const [loadingAttachments, setLoadingAttachments] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  void setCurrentFileIndex;
  const [showModal, setShowModal] = useState(false);
  
  const [asignarSupervisorId, setAsignarSupervisorId] = useState<string>('');
  const [clasificarCategoria, setClasificarCategoria] = useState('');
  const [clasificarPrioridad, setClasificarPrioridad] = useState('');
  const [clasificarComentario, setClasificarComentario] = useState('');
  const [resolverRespuesta, setResolverRespuesta] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [feedback, setFeedback] = useState('');

  const [activeTab, setActiveTab] = useState<'pendientes' | 'proceso' | 'resueltas'>('pendientes');

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      setLoading(true);
      setError('');
      
      try {
        let pqrsData: PQR[] = [];

        try {
          pqrsData = await pqrService.getAll();
        } catch {
          pqrsData = [];
        }

        let supervisorsData: UserListItem[] = [];
        if (isAdmin) {
          try {
            supervisorsData = await userService.getSupervisors();
          } catch {
            supervisorsData = [];
          }
        }

        if (isMounted) {
          setPqrs(pqrsData);
          if (isAdmin && supervisorsData.length > 0) {
            setSupervisors(supervisorsData);
          }
        }
      } catch (e: unknown) {
        if (isMounted) {
          setError('No fue posible cargar los datos. Verifique la conexión.');
          setPqrs([]);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();
    return () => { isMounted = false; };
  }, [isAdmin]);

  const loadHistory = async (pqrId: number) => {
    setLoadingHistory(true);
    try {
      const response = await fetch(`/api/historial/pqr/${pqrId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setHistory(data?.data || []);
    } catch {
      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadAttachments = async (pqrId: number) => {
    setLoadingAttachments(true);
    try {
      const files = await fileService.getByPqr(pqrId);
      setAttachments(files);
    } catch {
      setAttachments([]);
    } finally {
      setLoadingAttachments(false);
    }
  };

  const handleFileChange = (index: number) => {
    setCurrentFileIndex(index);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handlePreviewAttachment = (file: PQRFile) => {
    const index = attachments.findIndex(f => f.id === file.id);
    setCurrentFileIndex(index >= 0 ? index : 0);
    setShowViewer(true);
  };

  const filteredPqrs = pqrs.filter(p => {
    const estado = p.estado.toLowerCase();
    const search = searchText.trim().toLowerCase();
    const matchesSearch =
      !search ||
      p.titulo.toLowerCase().includes(search) ||
      p.descripcion.toLowerCase().includes(search) ||
      String(p.id).includes(search);
    if (!matchesSearch) return false;
    if (activeTab === 'pendientes') return estado === 'pendiente';
    if (activeTab === 'proceso') return estado === 'en_proceso';
    if (activeTab === 'resueltas') return ['resuelta', 'cerrada'].includes(estado);
    return true;
  });

  const handleVerDetalle = (pqr: PQR) => {
    setSelectedPqr(pqr);
    loadHistory(pqr.id);
    loadAttachments(pqr.id);
    setAsignarSupervisorId(pqr.supervisor_id?.toString() || '');
    setClasificarCategoria(pqr.categoria || '');
    setClasificarPrioridad(pqr.prioridad || '');
    setClasificarComentario('');
    setResolverRespuesta('');
    setShowModal(true);
  };

  const handleAsignar = async () => {
    if (!selectedPqr || !asignarSupervisorId) return;
    
    setActionLoading(true);
    try {
      const updated = await pqrService.asignar(selectedPqr.id, Number(asignarSupervisorId));
      setPqrs(pqrs.map(p => p.id === updated.id ? updated : p));
      setSelectedPqr(updated);
      loadHistory(updated.id);
      setFeedback('PQR asignada correctamente.');
    } catch {
      setFeedback('No fue posible asignar la PQR.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClasificar = async () => {
    if (!selectedPqr || !clasificarCategoria || !clasificarPrioridad) return;
    
    setActionLoading(true);
    try {
      const updated = await pqrService.clasificar(
        selectedPqr.id, 
        clasificarCategoria, 
        clasificarPrioridad, 
        clasificarComentario || undefined
      );
      setPqrs(pqrs.map(p => p.id === updated.id ? updated : p));
      setSelectedPqr(updated);
      loadHistory(updated.id);
      setClasificarComentario('');
      setFeedback('PQR clasificada correctamente.');
    } catch {
      setFeedback('No fue posible clasificar la PQR.');
    } finally {
      setActionLoading(false);
    }
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
    } catch {
      setFeedback('No fue posible resolver la PQR.');
    } finally {
      setActionLoading(false);
    }
  };

  const categorias = ['Facturacion', 'Tecnica', 'Servicio'];
  const prioridades = ['baja', 'media', 'alta', 'urgente'];

  const pendientesCount = pqrs.filter(p => p.estado.toLowerCase() === 'pendiente').length;
  const procesoCount = pqrs.filter(p => p.estado.toLowerCase() === 'en_proceso').length;
  const resueltasCount = pqrs.filter(p => ['resuelta', 'cerrada'].includes(p.estado.toLowerCase())).length;

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <div style={{ marginBottom: '16px' }}>Cargando...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">
          {isAdmin ? 'Gestión Operativa de PQRs' : 'Bandeja de Trabajo'}
        </h1>
        <p className="page-subtitle">
          {isAdmin 
            ? 'Asigne supervisores, clasifique y resuelva PQRs' 
            : 'Clasifique y resuelva las PQRs asignadas'}
        </p>
      </div>

      {error && (
        <div style={{ marginBottom: '20px', background: '#fee2e2', color: '#b91c1c', padding: '16px', borderRadius: '10px' }}>
          {error}
        </div>
      )}

      <div className="tabs" style={{ marginBottom: '20px' }}>
        <button className={`tab ${activeTab === 'pendientes' ? 'active' : ''}`} onClick={() => setActiveTab('pendientes')}>
          Pendientes ({pendientesCount})
        </button>
        <button className={`tab ${activeTab === 'proceso' ? 'active' : ''}`} onClick={() => setActiveTab('proceso')}>
          En Proceso ({procesoCount})
        </button>
        <button className={`tab ${activeTab === 'resueltas' ? 'active' : ''}`} onClick={() => setActiveTab('resueltas')}>
          Resueltas ({resueltasCount})
        </button>
      </div>

      {feedback ? (
        <div className="card" style={{ marginBottom: '14px', padding: '12px 14px', borderLeft: '4px solid #1e64c8' }}>
          <p style={{ fontSize: '13px', fontWeight: 600, color: '#1e293b' }}>{feedback}</p>
        </div>
      ) : null}

      <div className="card" style={{ marginBottom: '20px', padding: '16px', background: 'linear-gradient(180deg, #ffffff 0%, #f9fbff 100%)' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <label style={{ fontSize: '14px', fontWeight: '600' }}>Buscar:</label>
          <input 
            className="input" 
            style={{ width: '300px' }}
            placeholder="Buscar por titulo..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <span style={{ fontSize: '13px', color: '#6b7280' }}>
            ({filteredPqrs.length} PQRs)
          </span>
        </div>
      </div>

      {filteredPqrs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#9ca3af' }}>inbox</span>
          <p style={{ marginTop: '16px', color: '#6b7280' }}>No hay PQRs en esta categoria.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: '0' }}>
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
                <th>Asignada a</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredPqrs.map((pqr) => (
                <tr key={pqr.id}>
                  <td style={{ fontFamily: 'monospace' }}>#{pqr.id}</td>
                  <td style={{ fontSize: '13px' }}>{formatDate(pqr.created_at)}</td>
                  <td style={{ fontWeight: '500' }}>{pqr.titulo}</td>
                  <td style={{ textTransform: 'capitalize' }}>{pqr.tipo}</td>
                  <td>{pqr.categoria || '-'}</td>
                  <td>{pqr.prioridad || '-'}</td>
                  <td>
                    <span
                      className={`badge badge-${getEstadoBadge(pqr.estado)}`}
                      style={{
                        color: estadoVisual[pqr.estado]?.color || '#334155',
                        background: estadoVisual[pqr.estado]?.bg || '#f1f5f9',
                      }}
                    >
                      {pqr.estado.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{pqr.supervisor_id ? `Sup. #${pqr.supervisor_id}` : 'Sin asignar'}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleVerDetalle(pqr)}>
                      <span className="material-symbols-outlined">edit</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && selectedPqr && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <div className="modal-header">
              <h3>Gestión PQR #{selectedPqr.id}</h3>
              <button className="btn btn-ghost btn-sm" onClick={handleCloseModal}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73' }}>Titulo</p>
                    <p style={{ fontWeight: '600' }}>{selectedPqr.titulo}</p>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73' }}>Tipo</p>
                    <p style={{ textTransform: 'capitalize' }}>{selectedPqr.tipo}</p>
                  </div>
                </div>
                
                <div>
                  <p style={{ fontSize: '12px', color: '#525f73' }}>Descripción</p>
                  <p>{selectedPqr.descripcion}</p>
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span className="badge badge-primary">{selectedPqr.categoria || 'Sin categoría'}</span>
                  <span className="badge badge-warning">{selectedPqr.prioridad || 'Sin prioridad'}</span>
                  <span className={`badge badge-${getEstadoBadge(selectedPqr.estado)}`}>{selectedPqr.estado}</span>
                </div>

                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>Archivos adjuntos</h4>
                  {loadingAttachments ? (
                    <p style={{ color: '#6b7280' }}>Cargando adjuntos...</p>
                  ) : attachments.length === 0 ? (
                    <p style={{ color: '#6b7280' }}>Sin adjuntos.</p>
                  ) : (
                    <div style={{ display: 'grid', gap: '8px' }}>
                      {attachments.map((file) => (
                        <div key={file.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                          <div style={{ minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '13px', fontWeight: '600', wordBreak: 'break-all' }}>{file.nombre}</p>
                            <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#6b7280' }}>{file.tipo || 'application/octet-stream'}</p>
                          </div>
                          <button className="btn btn-secondary btn-sm" onClick={() => handlePreviewAttachment(file)}>
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {isAdmin && (
                  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>
                      <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', fontSize: '18px' }}>person_add</span>
                      Asignar a Supervisor
                    </h4>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select 
                        className="select" 
                        style={{ flex: 1 }}
                        value={asignarSupervisorId}
                        onChange={(e) => setAsignarSupervisorId(e.target.value)}
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
                      >
                        Asignar
                      </button>
                    </div>
                  </div>
                )}

                {isSupervisor && selectedPqr.estado === 'pendiente' && (
                  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>
                      <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', fontSize: '18px' }}>category</span>
                      Clasificar PQR
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <label style={{ fontSize: '12px', color: '#525f73' }}>Categoria</label>
                        <select 
                          className="select"
                          value={clasificarCategoria}
                          onChange={(e) => setClasificarCategoria(e.target.value)}
                        >
                          <option value="">Seleccionar...</option>
                          {categorias.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: '12px', color: '#525f73' }}>Prioridad</label>
                        <select 
                          className="select"
                          value={clasificarPrioridad}
                          onChange={(e) => setClasificarPrioridad(e.target.value)}
                        >
                          <option value="">Seleccionar...</option>
                          {prioridades.map(p => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div style={{ marginTop: '12px' }}>
                      <label style={{ fontSize: '12px', color: '#525f73' }}>Comentario (opcional)</label>
                      <input 
                        className="input"
                        placeholder="Agregar comentario..."
                        value={clasificarComentario}
                        onChange={(e) => setClasificarComentario(e.target.value)}
                      />
                    </div>
                    <button 
                      className="btn btn-primary"
                      style={{ marginTop: '12px' }}
                      onClick={handleClasificar}
                      disabled={actionLoading || !clasificarCategoria || !clasificarPrioridad}
                    >
                      Clasificar y Ponerse en Proceso
                    </button>
                  </div>
                )}

                {isSupervisor && selectedPqr.estado === 'en_proceso' && (
                  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>
                      <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', fontSize: '18px' }}>check_circle</span>
                      Resolver PQR
                    </h4>
                    <div>
                      <label style={{ fontSize: '12px', color: '#525f73' }}>Respuesta al usuario</label>
                      <textarea 
                        className="input"
                        rows={3}
                        placeholder="Escriba la respuesta al usuario..."
                        value={resolverRespuesta}
                        onChange={(e) => setResolverRespuesta(e.target.value)}
                      />
                    </div>
                    <button 
                      className="btn btn-success"
                      style={{ marginTop: '12px', backgroundColor: '#059669' }}
                      onClick={handleResolver}
                      disabled={actionLoading || !resolverRespuesta.trim()}
                    >
                      Marcar como Resuelta
                    </button>
                  </div>
                )}

                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>Historial</h4>
                  {loadingHistory ? (
                    <p style={{ color: '#6b7280' }}>Cargando...</p>
                  ) : history.length === 0 ? (
                    <p style={{ color: '#6b7280' }}>Sin historial.</p>
                  ) : (
                    <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
                      {history.map((h) => (
                        <div key={h.id} style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontWeight: '600', fontSize: '13px' }}>{h.accion}</span>
                            <span style={{ fontSize: '11px', color: '#6b7280' }}>{formatDate(h.created_at)}</span>
                          </div>
                          {h.detalle && <p style={{ fontSize: '12px', color: '#525f73', marginTop: '4px' }}>{h.detalle}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={handleCloseModal}>Cerrar</button>
            </div>
          </div>
        </div>
      )}

      {showViewer && attachments.length > 0 && (
        <div className="modal-overlay" onClick={() => setShowViewer(false)} style={{ zIndex: 300 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '90vw', width: '95%', maxHeight: '90vh', margin: '20px' }}>
            <div className="modal-header" style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Vista previa: {attachments[currentFileIndex]?.nombre}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowViewer(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body" style={{ padding: 0, height: 'calc(90vh - 80px)', overflow: 'hidden' }}>
              <ModalVisualizador
                isOpen={showViewer}
                onClose={() => setShowViewer(false)}
                files={attachments}
                currentFileIndex={currentFileIndex}
                onFileChange={handleFileChange}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
