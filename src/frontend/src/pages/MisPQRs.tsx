import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { fileService } from '../services/fileService';
import { pqrService } from '../services/pqrService';
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

export function MisPQRs() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPqr, setSelectedPqr] = useState<PQR | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [attachments, setAttachments] = useState<PQRFile[]>([]);
  const [loadingAttachments, setLoadingAttachments] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [showModal, setShowModal] = useState(false);

  const userId = Number(user?.id);

  useEffect(() => {
    let isMounted = true;

    const loadPqrs = async () => {
      if (!userId) {
        setError('Usuario no identificado.');
        setLoading(false);
        return;
      }

      try {
        const data = await pqrService.getAll({ usuario_id: userId });
        if (isMounted) {
          setPqrs(data);
        }
      } catch {
        if (isMounted) {
          setError('No fue posible cargar sus PQRs.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadPqrs();
    return () => { isMounted = false; };
  }, [userId]);

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

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handlePreviewAttachment = (file: PQRFile) => {
    const index = attachments.findIndex(f => f.id === file.id);
    setCurrentFileIndex(index >= 0 ? index : 0);
    setShowViewer(true);
  };

  const handleFileChange = (index: number) => {
    setCurrentFileIndex(index);
  };

  const handleVerDetalle = (pqr: PQR) => {
    setSelectedPqr(pqr);
    loadHistory(pqr.id);
    loadAttachments(pqr.id);
    setShowModal(true);
  };

  const handleCerrar = async (pqrId: number) => {
    if (!confirm('¿Está seguro que desea cerrar esta PQR?')) return;

    try {
      await pqrService.cerrar(pqrId);
      setPqrs(pqrs.map(p => p.id === pqrId ? { ...p, estado: 'cerrada' } : p));
      setShowModal(false);
    } catch {
      alert('No fue posible cerrar la PQR.');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <p>Cargando...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Mis PQRs</h1>
          <p className="page-subtitle">Consulte el estado de sus solicitudes</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/registro-pqr')}>
          <span className="material-symbols-outlined">add</span>
          Nueva PQR
        </button>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '20px' }}>{error}</div>
      )}

      {pqrs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#9ca3af' }}>inbox</span>
          <p style={{ marginTop: '16px', color: '#6b7280' }}>No tiene PQRs registradas.</p>
          <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => navigate('/registro-pqr')}>
            Crear mi primera PQR
          </button>
        </div>
      ) : (
        <div className="card" style={{ padding: '0' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Titulo</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th>Prioridad</th>
                <th>Estado</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pqrs.map((pqr) => (
                <tr key={pqr.id}>
                  <td style={{ fontFamily: 'monospace' }}>#{pqr.id}</td>
                  <td>{pqr.titulo}</td>
                  <td style={{ textTransform: 'capitalize' }}>{pqr.tipo}</td>
                  <td>{pqr.categoria || '-'}</td>
                  <td>{pqr.prioridad || '-'}</td>
                  <td>
                    <span className={`badge badge-${getEstadoBadge(pqr.estado)}`}>
                      {pqr.estado.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{formatDate(pqr.created_at)}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleVerDetalle(pqr)}>
                      <span className="material-symbols-outlined">visibility</span>
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
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3>PQR #{selectedPqr.id}</h3>
              <button className="btn btn-ghost btn-sm" onClick={handleCloseModal}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: '16px' }}>
                <div>
                  <p style={{ fontSize: '12px', color: '#525f73' }}>Titulo</p>
                  <p style={{ fontWeight: '600' }}>{selectedPqr.titulo}</p>
                </div>
                <div>
                  <p style={{ fontSize: '12px', color: '#525f73' }}>Descripción</p>
                  <p>{selectedPqr.descripcion}</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{selectedPqr.tipo}</span>
                  <span className="badge badge-primary">{selectedPqr.categoria || 'Sin categoria'}</span>
                  <span className="badge badge-warning">{selectedPqr.prioridad || 'Sin prioridad'}</span>
                  <span className={`badge badge-${getEstadoBadge(selectedPqr.estado)}`}>{selectedPqr.estado}</span>
                </div>

                <div style={{ marginTop: '16px' }}>
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

                <div style={{ marginTop: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px' }}>Historial</h4>
                  {loadingHistory ? (
                    <p style={{ color: '#6b7280' }}>Cargando historial...</p>
                  ) : history.length === 0 ? (
                    <p style={{ color: '#6b7280' }}>Sin historial.</p>
                  ) : (
                    <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      {history.map((h) => (
                        <div key={h.id} style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
              {selectedPqr.estado === 'resuelta' && (
                <button className="btn btn-primary" onClick={() => handleCerrar(selectedPqr.id)}>
                  Cerrar PQR
                </button>
              )}
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
