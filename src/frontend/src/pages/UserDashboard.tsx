import { useEffect, useMemo, useState, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { pqrService } from '../services/pqrService';
import { fileService } from '../services/fileService';
import { ModalVisualizador } from '../components/visualizador/ModalVisualizador';
import api from '../services/api';
import type { PQR, PQRFile } from '../types';

interface HistoryEntry {
  id: number;
  pqr_id: number;
  usuario_id: number | null;
  accion: string;
  detalle: string | null;
  created_at: string;
}

interface RecommendedAction {
  key: string;
  icon: string;
  title: string;
  description: string;
  cta: string;
  run: () => void;
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

const estadoColors: Record<string, { bg: string; text: string; icon: string }> = {
  pendiente: { bg: '#fef3c7', text: '#92400e', icon: 'pending' },
  en_proceso: { bg: '#dbeafe', text: '#003d9b', icon: 'schedule' },
  resuelta: { bg: '#dcfce7', text: '#166534', icon: 'check_circle' },
  cerrada: { bg: '#f3f4f6', text: '#525f73', icon: 'done_all' }
};

export function UserDashboard() {
  const { user } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tabs state
  const [activeTab, setActiveTab] = useState<'lista' | 'crear' | 'respuestas'>('lista');

  // Create PQR state
  const [createStep, setCreateStep] = useState<1 | 2>(1);
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState('');
  const [createSuccess, setCreateSuccess] = useState('');

  const [formData, setFormData] = useState({
    tipo: '',
    titulo: '',
    descripcion: '',
  });

  const [adjuntos, setAdjuntos] = useState<File[]>([]);

  // List PQRs state
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPqr, setSelectedPqr] = useState<PQR | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [attachments, setAttachments] = useState<PQRFile[]>([]);
  const [loadingAttachments, setLoadingAttachments] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<'todos' | 'pendiente' | 'en_proceso' | 'resuelta' | 'cerrada'>('todos');

  const userId = Number(user?.id);

  const tipos = [
    { value: 'peticion', label: 'Petición', icon: 'edit_note', color: '#059669', bg: '#d1fae5', desc: 'Solicitud de información' },
    { value: 'queja', label: 'Queja', icon: 'sentiment_dissatisfied', color: '#dc2626', bg: '#fee2e2', desc: 'Expresar inconformidad' },
    { value: 'reclamo', label: 'Reclamo', icon: 'warning', color: '#d97706', bg: '#fef3c7', desc: 'Protesta formal' },
  ];

  const currentUserId = useMemo(() => {
    const id = Number(user?.id);
    return Number.isFinite(id) ? id : null;
  }, [user?.id]);

  const canContinue = useMemo(() => {
    if (createStep === 1) return Boolean(formData.tipo);
    if (createStep === 2) return Boolean(formData.titulo.trim() && formData.descripcion.trim().length >= 10);
    return true;
  }, [formData, createStep]);

  const sortedByDateDesc = useMemo(() => {
    return [...pqrs].sort((a, b) => {
      const aDate = new Date(a.updated_at || a.created_at || '').getTime();
      const bDate = new Date(b.updated_at || b.created_at || '').getTime();
      return (Number.isFinite(bDate) ? bDate : 0) - (Number.isFinite(aDate) ? aDate : 0);
    });
  }, [pqrs]);

  // Load PQRs on mount
  useEffect(() => {
    let isMounted = true;

    const loadPqrs = async () => {
      if (!userId) {
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
          setPqrs([]);
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
      const response = await api.get(`/historial/pqr/${pqrId}`);
      setHistory(response.data?.data || []);
    } catch {
      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleVerDetalle = (pqr: PQR) => {
    setSelectedPqr(pqr);
    loadHistory(pqr.id);
    loadAttachments(pqr.id);
    setShowModal(true);
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

  const handleViewerFileChange = (index: number) => {
    setCurrentFileIndex(index);
  };

  const handleCerrar = async (pqrId: number) => {
    if (!confirm('¿Está seguro que desea cerrar esta solicitud?')) return;

    try {
      await pqrService.cerrar(pqrId);
      setPqrs(pqrs.map(p => p.id === pqrId ? { ...p, estado: 'cerrada' } : p));
      setShowModal(false);
    } catch {
      alert('No fue posible cerrar la solicitud.');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAdjuntos([...adjuntos, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAdjuntos(adjuntos.filter((_, i) => i !== index));
  };

  const handleCreateSubmit = async () => {
    if (!currentUserId) {
      setCreateError('No se pudo identificar el usuario.');
      return;
    }

    setSubmitting(true);
    setCreateError('');

    try {
      const created = await pqrService.create({
        tipo: formData.tipo,
        titulo: formData.titulo.trim(),
        descripcion: formData.descripcion.trim(),
        estado: 'pendiente',
        usuario_id: currentUserId,
      });

      if (created?.id && adjuntos.length > 0) {
        await Promise.all(adjuntos.map((file) => fileService.uploadToPqr(created.id, file)));
      }

      setPqrs([created, ...pqrs]);
      setCreateSuccess(`✓ Solicitud #${created.id} enviada correctamente`);

      // Reset form
      setCreateStep(1);
      setFormData({ tipo: '', titulo: '', descripcion: '' });
      setAdjuntos([]);

      // Go to list tab
      setTimeout(() => {
        setActiveTab('lista');
        setCreateSuccess('');
      }, 2000);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setCreateError(e.response?.data?.message || e.response?.data?.detail || 'No fue posible registrar la solicitud.');
    } finally {
      setSubmitting(false);
    }
  };

  const resueltas = pqrs.filter(p => p.estado === 'resuelta');
  const pendientes = pqrs.filter(p => p.estado === 'pendiente').length;
  const proceso = pqrs.filter(p => p.estado === 'en_proceso').length;
  const cerradas = pqrs.filter((p) => p.estado === 'cerrada').length;
  const totalResueltasOCerradas = pqrs.filter((p) => p.estado === 'resuelta' || p.estado === 'cerrada').length;
  const tasaResolucion = pqrs.length > 0 ? Math.round((totalResueltasOCerradas / pqrs.length) * 100) : 0;
  const pqrsFiltradas = pqrs.filter((p) => {
    if (statusFilter !== 'todos' && p.estado !== statusFilter) {
      return false;
    }
    const q = searchText.trim().toLowerCase();
    if (!q) {
      return true;
    }
    const text = `${p.id} ${p.titulo} ${p.descripcion} ${p.tipo}`.toLowerCase();
    return text.includes(q);
  });
  const prioridadUrgenteOAlta = pqrs.filter((p) => ['urgente', 'alta'].includes((p.prioridad || '').toLowerCase())).length;
  const pqrMasReciente = sortedByDateDesc[0] || null;
  const pqrPendienteMasAntigua = pqrs
    .filter((p) => p.estado === 'pendiente')
    .sort((a, b) => {
      const aDate = new Date(a.created_at || '').getTime();
      const bDate = new Date(b.created_at || '').getTime();
      return (Number.isFinite(aDate) ? aDate : 0) - (Number.isFinite(bDate) ? bDate : 0);
    })[0] || null;

  const recommendedActions: RecommendedAction[] = useMemo(() => {
    const actions: RecommendedAction[] = [];

    if (pqrPendienteMasAntigua) {
      actions.push({
        key: 'pending-follow-up',
        icon: 'schedule_send',
        title: `Solicitud #${pqrPendienteMasAntigua.id} pendiente de atención`,
        description: 'Te recomendamos revisar el detalle y aportar información adicional si aplica.',
        cta: 'Ver detalle',
        run: () => handleVerDetalle(pqrPendienteMasAntigua),
      });
    }

    const pqrResuelta = sortedByDateDesc.find((p) => p.estado === 'resuelta');
    if (pqrResuelta) {
      actions.push({
        key: 'close-resolved',
        icon: 'check_circle',
        title: `Solicitud #${pqrResuelta.id} lista para cierre`,
        description: 'Si estás conforme con la respuesta, puedes cerrarla y dejar trazabilidad completa.',
        cta: 'Revisar y cerrar',
        run: () => handleVerDetalle(pqrResuelta),
      });
    }

    if (!actions.length) {
      actions.push({
        key: 'create-new',
        icon: 'edit_square',
        title: 'No hay acciones urgentes pendientes',
        description: 'Puedes crear una nueva solicitud o revisar el historial de tus casos cerrados.',
        cta: 'Crear solicitud',
        run: () => setActiveTab('crear'),
      });
    }

    return actions.slice(0, 2);
  }, [pqrPendienteMasAntigua, sortedByDateDesc]);

  const priorityCases = useMemo(() => {
    return sortedByDateDesc
      .filter((p) => ['urgente', 'alta'].includes((p.prioridad || '').toLowerCase()))
      .slice(0, 3);
  }, [sortedByDateDesc]);

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)' }}>
      {/* Navbar */}
      <div style={{
        background: 'linear-gradient(135deg, #003d9b 0%, #0052cc 100%)',
        color: '#fff',
        padding: '24px',
        boxShadow: '0 4px 12px rgba(0, 61, 155, 0.15)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', margin: '0', letterSpacing: '-0.5px' }}>Mi Centro de Solicitudes</h1>
          <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.8)', margin: '6px 0 0 0' }}>Bienvenido de vuelta, {user?.full_name || 'Usuario'}</p>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            useAuthStore.getState().logout();
            window.location.href = '/login';
          }}
          style={{ background: 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)', color: '#fff' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>logout</span>
        </button>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '18px 24px 0' }}>
        <div className="card" style={{ padding: '12px 16px', background: 'linear-gradient(90deg, #ecf4ff 0%, #f7fbff 100%)', borderLeft: '4px solid #1e64c8' }}>
          <p style={{ fontSize: '13px', color: '#1553a1', fontWeight: 600 }}>
            Portal ciudadano: seguimiento claro de solicitudes, historial y respuestas oficiales.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginTop: '12px' }}>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Solicitudes totales</p>
            <p style={{ fontSize: '28px', color: '#0f172a', fontWeight: 800, margin: '8px 0 0' }}>{pqrs.length}</p>
          </div>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>En atención</p>
            <p style={{ fontSize: '28px', color: '#1553a1', fontWeight: 800, margin: '8px 0 0' }}>{pendientes + proceso}</p>
          </div>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Resueltas/Cerradas</p>
            <p style={{ fontSize: '28px', color: '#166534', fontWeight: 800, margin: '8px 0 0' }}>{totalResueltasOCerradas}</p>
          </div>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Tasa de resolución</p>
            <p style={{ fontSize: '28px', color: '#0f766e', fontWeight: 800, margin: '8px 0 0' }}>{tasaResolucion}%</p>
          </div>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Prioridad alta/urgente</p>
            <p style={{ fontSize: '28px', color: '#9a3412', fontWeight: 800, margin: '8px 0 0' }}>{prioridadUrgenteOAlta}</p>
          </div>
          <div className="card" style={{ padding: '14px 16px' }}>
            <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Cerradas</p>
            <p style={{ fontSize: '28px', color: '#334155', fontWeight: 800, margin: '8px 0 0' }}>{cerradas}</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginTop: '12px' }}>
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <p style={{ fontSize: '12px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Siguiente acción recomendada</p>
              <span className="badge badge-primary" style={{ fontSize: '11px' }}>Asistente IA-ready</span>
            </div>
            <div style={{ display: 'grid', gap: '10px' }}>
              {recommendedActions.map((action) => (
                <div key={action.key} style={{ border: '1px solid #e2e8f0', borderRadius: '12px', padding: '12px', background: '#f8fbff' }}>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'start' }}>
                    <span className="material-symbols-outlined" style={{ color: '#1553a1', fontSize: '20px' }}>{action.icon}</span>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{action.title}</p>
                      <p style={{ margin: '4px 0 10px', fontSize: '13px', color: '#64748b' }}>{action.description}</p>
                      <button className="btn btn-secondary btn-sm" onClick={action.run}>{action.cta}</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <p style={{ fontSize: '12px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Casos prioritarios</p>
              <span style={{ fontSize: '12px', color: '#9a3412', fontWeight: 700 }}>{priorityCases.length} en foco</span>
            </div>
            {priorityCases.length === 0 ? (
              <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>No tienes solicitudes de prioridad alta o urgente actualmente.</p>
            ) : (
              <div style={{ display: 'grid', gap: '8px' }}>
                {priorityCases.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleVerDetalle(p)}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '10px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '10px',
                      padding: '10px 12px',
                      background: '#ffffff',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ textAlign: 'left' }}>
                      <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>#{p.id} · {p.titulo}</p>
                      <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>{p.tipo} · {formatDate(p.created_at)}</p>
                    </div>
                    <span className="badge badge-warning" style={{ textTransform: 'capitalize' }}>{p.prioridad || 'alta'}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card" style={{ marginTop: '12px', padding: '14px 16px' }}>
          <p style={{ fontSize: '12px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>Actividad más reciente</p>
          {pqrMasReciente ? (
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
              <p style={{ margin: 0, fontSize: '13px', color: '#1e293b' }}>
                Último movimiento en solicitud <strong>#{pqrMasReciente.id}</strong>: {pqrMasReciente.titulo}
              </p>
              <button className="btn btn-ghost btn-sm" onClick={() => handleVerDetalle(pqrMasReciente)}>
                Ver trazabilidad
              </button>
            </div>
          ) : (
            <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#64748b' }}>Aún no hay actividad reciente en tus solicitudes.</p>
          )}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{
        background: '#fff',
        borderBottom: '2px solid #e5e7eb',
        padding: '0 24px'
      }}>
        <div style={{ display: 'flex', gap: '0', maxWidth: '1400px', margin: '0 auto' }}>
          {[
            { id: 'lista', icon: 'inbox', label: 'Mis Solicitudes', count: pqrs.length },
            { id: 'crear', icon: 'add_circle_outline', label: 'Nueva Solicitud', count: null },
            { id: 'respuestas', icon: 'mail_outline', label: 'Respuestas', count: resueltas.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '20px 24px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '15px',
                fontWeight: activeTab === tab.id ? '700' : '600',
                color: activeTab === tab.id ? '#003d9b' : '#6b7280',
                borderBottomWidth: activeTab === tab.id ? '3px' : '0',
                borderBottomColor: '#003d9b',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                whiteSpace: 'nowrap',
                position: 'relative',
                transition: 'all 0.3s'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span style={{
                  background: activeTab === tab.id ? '#003d9b' : '#e5e7eb',
                  color: activeTab === tab.id ? '#fff' : '#525f73',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '700'
                }}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '40px 24px', maxWidth: '1400px', margin: '0 auto' }}>

        {/* Lista Tab */}
        {activeTab === 'lista' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '16px' }}>
              <input
                className="input"
                style={{ width: '320px', maxWidth: '100%' }}
                placeholder="Buscar por ID, asunto o descripción..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              <select className="select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)} style={{ width: '220px' }}>
                <option value="todos">Todos los estados</option>
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En proceso</option>
                <option value="resuelta">Resuelta</option>
                <option value="cerrada">Cerrada</option>
              </select>
            </div>

            {/* Stats Cards */}
            {!loading && pqrs.length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  background: '#fff',
                  borderRadius: '16px',
                  padding: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  borderLeft: '4px solid #003d9b'
                }}>
                  <p style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', margin: '0' }}>Total</p>
                  <p style={{ fontSize: '32px', fontWeight: '800', color: '#003d9b', margin: '12px 0 0 0' }}>{pqrs.length}</p>
                </div>

                {pendientes > 0 && (
                  <div style={{
                    background: '#fff',
                    borderRadius: '16px',
                    padding: '24px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    borderLeft: '4px solid #d97706'
                  }}>
                    <p style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', margin: '0' }}>Pendientes</p>
                    <p style={{ fontSize: '32px', fontWeight: '800', color: '#d97706', margin: '12px 0 0 0' }}>{pendientes}</p>
                  </div>
                )}

                {proceso > 0 && (
                  <div style={{
                    background: '#fff',
                    borderRadius: '16px',
                    padding: '24px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    borderLeft: '4px solid #0ea5e9'
                  }}>
                    <p style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', margin: '0' }}>En proceso</p>
                    <p style={{ fontSize: '32px', fontWeight: '800', color: '#0ea5e9', margin: '12px 0 0 0' }}>{proceso}</p>
                  </div>
                )}

                <div style={{
                  background: '#fff',
                  borderRadius: '16px',
                  padding: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                  borderLeft: '4px solid #10b981'
                }}>
                  <p style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', margin: '0' }}>Resueltas</p>
                  <p style={{ fontSize: '32px', fontWeight: '800', color: '#10b981', margin: '12px 0 0 0' }}>{pqrs.filter(p => p.estado === 'resuelta' || p.estado === 'cerrada').length}</p>
                </div>
              </div>
            )}

            {loading ? (
              <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#d1d5db', marginBottom: '16px' }}>hourglass_empty</span>
                <p style={{ color: '#6b7280', fontSize: '16px' }}>Cargando tus solicitudes...</p>
              </div>
            ) : pqrsFiltradas.length === 0 ? (
              <div style={{
                background: '#fff',
                borderRadius: '20px',
                textAlign: 'center',
                padding: '60px 20px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '56px', color: '#d1d5db', marginBottom: '16px' }}>inbox</span>
                <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: '0 0 12px 0' }}>
                  {pqrs.length === 0 ? 'Aún no tienes solicitudes' : 'No hay resultados con ese filtro'}
                </h3>
                <p style={{ color: '#6b7280', fontSize: '15px', margin: '0 0 24px 0' }}>
                  {pqrs.length === 0 ? 'Crea tu primera solicitud para comenzar' : 'Prueba otro estado o una búsqueda más general.'}
                </p>
                <button className="btn btn-primary" onClick={() => setActiveTab('crear')} style={{ fontSize: '14px', fontWeight: '600' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add_circle</span>
                  Crear solicitud
                </button>
              </div>
            ) : (
              <div style={{
                background: '#fff',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <div style={{ overflowX: 'auto' }}>
                  <table className="table" style={{ marginBottom: '0' }}>
                    <thead>
                      <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>ID</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>Asunto</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>Tipo</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>Categoría</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>Estado</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}>Fecha</th>
                        <th style={{ fontWeight: '700', color: '#1f2937' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {pqrsFiltradas.map((pqr, idx) => (
                        <tr key={pqr.id} style={{ borderBottom: idx < pqrsFiltradas.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
                          <td style={{ fontFamily: 'monospace', fontWeight: '700', color: '#003d9b' }}>#{pqr.id}</td>
                          <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '15px', fontWeight: '500' }}>{pqr.titulo}</td>
                          <td style={{ textTransform: 'capitalize', fontSize: '13px', color: '#6b7280' }}>{pqr.tipo}</td>
                          <td style={{ fontSize: '13px', color: '#6b7280' }}>{pqr.categoria || '-'}</td>
                          <td>
                            <div style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '6px 12px',
                              borderRadius: '8px',
                              background: estadoColors[pqr.estado]?.bg || '#f3f4f6',
                              color: estadoColors[pqr.estado]?.text || '#525f73',
                              fontSize: '12px',
                              fontWeight: '600'
                            }}>
                              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                                {estadoColors[pqr.estado]?.icon || 'help'}
                              </span>
                              {pqr.estado.replace('_', ' ')}
                            </div>
                          </td>
                          <td style={{ fontSize: '13px', color: '#6b7280', whiteSpace: 'nowrap' }}>{formatDate(pqr.created_at)}</td>
                          <td>
                            <button
                              className="btn btn-ghost btn-sm"
                              onClick={() => handleVerDetalle(pqr)}
                              title="Ver detalles"
                              style={{ color: '#003d9b' }}
                            >
                              <span className="material-symbols-outlined">visibility</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Crear Tab */}
        {activeTab === 'crear' && (
          <div className="animate-fade-in">
            <div style={{
              background: '#fff',
              borderRadius: '20px',
              padding: '40px',
              maxWidth: '800px',
              margin: '0 auto',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
            }}>
              <h2 style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px', color: '#1f2937' }}>Crear Nueva Solicitud</h2>
              <p style={{ color: '#6b7280', margin: '0 0 32px 0' }}>Completa los campos para registrar tu solicitud</p>

              {/* Step indicator */}
              <div style={{ display: 'flex', gap: '20px', marginBottom: '40px' }}>
                {[1, 2].map((step) => (
                  <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      background: createStep >= step ? 'linear-gradient(135deg, #003d9b 0%, #0052cc 100%)' : '#e5e7eb',
                      color: createStep >= step ? '#fff' : '#9ca3af',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px',
                      fontWeight: '700',
                      boxShadow: createStep >= step ? '0 4px 12px rgba(0, 61, 155, 0.3)' : 'none'
                    }}>
                      {createStep > step ? '✓' : step}
                    </div>
                    <span style={{ color: createStep >= step ? '#003d9b' : '#9ca3af', fontWeight: '600', fontSize: '15px' }}>
                      {step === 1 ? 'Tipo y Asunto' : 'Confirmación'}
                    </span>
                  </div>
                ))}
              </div>

              {createSuccess && (
                <div style={{
                  background: '#dcfce7',
                  color: '#166534',
                  padding: '16px',
                  borderRadius: '12px',
                  marginBottom: '24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>check_circle</span>
                  {createSuccess}
                </div>
              )}

              {createError && (
                <div style={{
                  background: '#fee2e2',
                  color: '#991b1b',
                  padding: '16px',
                  borderRadius: '12px',
                  marginBottom: '24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>error</span>
                  {createError}
                </div>
              )}

              {/* Step 1 */}
              {createStep === 1 && (
                <div style={{ animation: 'fadeIn 0.3s ease' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '20px', color: '#1f2937' }}>Selecciona el tipo de solicitud</h3>
                  <div style={{ display: 'grid', gap: '12px', marginBottom: '32px' }}>
                    {tipos.map((tipo) => (
                      <button
                        key={tipo.value}
                        onClick={() => setFormData({ ...formData, tipo: tipo.value })}
                        style={{
                          padding: '20px',
                          borderRadius: '12px',
                          border: `2px solid ${formData.tipo === tipo.value ? tipo.color : '#e5e7eb'}`,
                          background: formData.tipo === tipo.value ? tipo.bg : '#fff',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.2s'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '32px', color: tipo.color }}>
                            {tipo.icon}
                          </span>
                          <div>
                            <p style={{ fontWeight: '700', color: tipo.color, margin: '0', fontSize: '16px' }}>{tipo.label}</p>
                            <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{tipo.desc}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>

                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#1f2937', marginBottom: '10px' }}>ASUNTO *</label>
                    <input
                      className="input"
                      placeholder="Resumen breve de tu solicitud"
                      value={formData.titulo}
                      onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                      style={{ fontSize: '15px', padding: '12px' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#1f2937', marginBottom: '10px' }}>DESCRIPCIÓN *</label>
                    <textarea
                      className="input"
                      rows={5}
                      placeholder="Cuéntanos los detalles de tu solicitud..."
                      value={formData.descripcion}
                      onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                      style={{ fontSize: '15px', padding: '12px', resize: 'vertical' }}
                    />
                    <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
                      {formData.descripcion.length} caracteres (mínimo 10)
                    </p>
                  </div>

                  <div style={{ marginTop: '20px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#1f2937', marginBottom: '10px' }}>ADJUNTOS (OPCIONAL)</label>
                    <div
                      style={{
                        border: '2px dashed #d1d5db',
                        borderRadius: '12px',
                        padding: '32px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        background: '#f9fafb'
                      }}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: '40px', color: '#9ca3af', marginBottom: '12px' }}>cloud_upload</span>
                      <p style={{ marginTop: '8px', color: '#6b7280', fontSize: '14px', fontWeight: '500' }}>Arrastra archivos aquí o haz clic para seleccionar</p>
                      <p style={{ fontSize: '12px', color: '#9ca3af', margin: '4px 0 0 0' }}>PNG, JPG, PDF (máx. 10MB cada uno)</p>
                      <input ref={fileInputRef} type="file" multiple accept="image/*,.pdf" style={{ display: 'none' }} onChange={handleFileChange} />
                    </div>
                    {adjuntos.length > 0 && (
                      <div style={{ marginTop: '16px' }}>
                        {adjuntos.map((file, i) => (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: '#f3f4f6', borderRadius: '8px', marginBottom: '8px' }}>
                            <span style={{ fontSize: '14px', fontWeight: '500' }}>{file.name}</span>
                            <button
                              type="button"
                              onClick={() => removeFile(i)}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}
                            >
                              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>close</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Step 2 */}
              {createStep === 2 && (
                <div style={{ animation: 'fadeIn 0.3s ease' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '24px', color: '#1f2937' }}>Revisa los datos de tu solicitud</h3>
                  <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '24px', display: 'grid', gap: '20px' }}>
                    <div style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '16px' }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: '700', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Tipo</p>
                      <span className="badge badge-primary" style={{
                        background: tipos.find(t => t.value === formData.tipo)?.bg,
                        color: tipos.find(t => t.value === formData.tipo)?.color,
                        padding: '8px 14px',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '600'
                      }}>
                        {tipos.find(t => t.value === formData.tipo)?.label || '-'}
                      </span>
                    </div>

                    <div style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '16px' }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: '700', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Asunto</p>
                      <p style={{ fontWeight: '600', margin: '0', fontSize: '16px', color: '#1f2937' }}>{formData.titulo || '-'}</p>
                    </div>

                    <div style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '16px' }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: '700', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Descripción</p>
                      <p style={{ fontSize: '15px', lineHeight: '1.6', color: '#525f73', marginTop: '0', marginBottom: '0' }}>{formData.descripcion || '-'}</p>
                    </div>

                    {adjuntos.length > 0 && (
                      <div>
                        <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: '700', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Archivos adjuntos</p>
                        <p style={{ fontWeight: '600', margin: '0', fontSize: '15px', color: '#10b981' }}>{adjuntos.length} archivo(s) para enviar</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Navigation buttons */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '40px', justifyContent: 'flex-end' }}>
                {createStep > 1 && (
                  <button className="btn btn-secondary" onClick={() => setCreateStep(1)} disabled={submitting} style={{ fontWeight: '600' }}>
                    ← Atrás
                  </button>
                )}
                {createStep === 1 && (
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      if (!formData.tipo || !formData.titulo.trim() || formData.descripcion.trim().length < 10) {
                        setCreateError('Completa tipo, asunto y una descripción mínima de 10 caracteres.');
                        return;
                      }
                      setCreateError('');
                      setCreateStep(2);
                    }}
                    disabled={submitting}
                    style={{ fontWeight: '600' }}
                  >
                    Siguiente →
                  </button>
                )}
                {createStep === 2 && (
                  <button className="btn btn-primary" onClick={handleCreateSubmit} disabled={submitting || !canContinue} style={{ fontWeight: '600' }}>
                    {submitting ? 'Enviando...' : 'Enviar Solicitud'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Respuestas Tab */}
        {activeTab === 'respuestas' && (
          <div className="animate-fade-in">
            {loading ? (
              <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#d1d5db', marginBottom: '16px' }}>hourglass_empty</span>
                <p style={{ color: '#6b7280', fontSize: '16px' }}>Cargando respuestas...</p>
              </div>
            ) : resueltas.length === 0 ? (
              <div style={{
                background: '#fff',
                borderRadius: '20px',
                textAlign: 'center',
                padding: '60px 20px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '56px', color: '#d1d5db', marginBottom: '16px' }}>mail_outline</span>
                <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: '0 0 12px 0' }}>Aún no tienes respuestas</h3>
                <p style={{ color: '#6b7280', fontSize: '15px', margin: '0' }}>Las respuestas aparecerán aquí cuando tus solicitudes sean resueltas</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '16px' }}>
                {resueltas.map((pqr) => (
                  <div key={pqr.id} style={{
                    background: '#fff',
                    borderRadius: '16px',
                    padding: '24px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    borderLeft: '4px solid #10b981'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
                      <div>
                        <h3 style={{ fontSize: '18px', fontWeight: '700', margin: '0 0 6px 0', color: '#1f2937' }}>Solicitud #{pqr.id}</h3>
                        <p style={{ fontSize: '14px', color: '#6b7280', margin: '0' }}>Asunto: {pqr.titulo}</p>
                      </div>
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 14px',
                        borderRadius: '8px',
                        background: '#dcfce7',
                        color: '#166534',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}>
                        <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>check_circle</span>
                        Resuelto
                      </div>
                    </div>
                    <p style={{ color: '#525f73', margin: '12px 0', lineHeight: '1.6', fontSize: '15px' }}>{pqr.descripcion}</p>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleVerDetalle(pqr)}
                      style={{ color: '#003d9b', marginTop: '12px', fontWeight: '600' }}
                    >
                      <span className="material-symbols-outlined">visibility</span>
                      Ver detalles y historial
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal for details */}
      {showModal && selectedPqr && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <div className="modal-header" style={{ background: '#f8fafc', borderBottom: '2px solid #e5e7eb' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '700', margin: '0', color: '#1f2937' }}>Solicitud #{selectedPqr.id}</h3>
                <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{selectedPqr.titulo}</p>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={handleCloseModal}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'grid', gap: '20px' }}>
                <div>
                  <p style={{ fontSize: '12px', color: '#6b7280', fontWeight: '700', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Descripción</p>
                  <p style={{ lineHeight: '1.6', color: '#525f73', margin: '0', fontSize: '15px' }}>{selectedPqr.descripcion}</p>
                </div>

                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    background: '#f3f4f6',
                    color: '#525f73',
                    fontSize: '13px',
                    fontWeight: '600'
                  }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>category</span>
                    {selectedPqr.tipo}
                  </div>

                  {selectedPqr.categoria && (
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: '8px',
                      background: '#dbeafe',
                      color: '#003d9b',
                      fontSize: '13px',
                      fontWeight: '600'
                    }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>label</span>
                      {selectedPqr.categoria}
                    </div>
                  )}

                  {selectedPqr.prioridad && (
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: '8px',
                      background: '#fef3c7',
                      color: '#92400e',
                      fontSize: '13px',
                      fontWeight: '600'
                    }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>flag</span>
                      {selectedPqr.prioridad}
                    </div>
                  )}

                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    background: estadoColors[selectedPqr.estado]?.bg,
                    color: estadoColors[selectedPqr.estado]?.text,
                    fontSize: '13px',
                    fontWeight: '600'
                  }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                      {estadoColors[selectedPqr.estado]?.icon}
                    </span>
                    {selectedPqr.estado.replace('_', ' ')}
                  </div>
                </div>

                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '16px', color: '#1f2937' }}>Archivos adjuntos</h4>
                  {loadingAttachments ? (
                    <p style={{ color: '#6b7280', fontSize: '14px', margin: '0' }}>Cargando adjuntos...</p>
                  ) : attachments.length === 0 ? (
                    <p style={{ color: '#6b7280', fontSize: '14px', margin: '0' }}>Sin adjuntos.</p>
                  ) : (
                    <div style={{ display: 'grid', gap: '8px', marginBottom: '16px' }}>
                      {attachments.map((file) => (
                        <div key={file.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                          <div style={{ minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: '#1f2937', wordBreak: 'break-all' }}>{file.nombre}</p>
                            <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#6b7280' }}>{file.tipo || 'application/octet-stream'}</p>
                          </div>
                          <button className="btn btn-sm btn-secondary" onClick={() => handlePreviewAttachment(file)}>
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '16px', color: '#1f2937' }}>Historial de cambios</h4>
                  {loadingHistory ? (
                    <p style={{ color: '#6b7280', fontSize: '14px', margin: '0' }}>Cargando historial...</p>
                  ) : history.length === 0 ? (
                    <p style={{ color: '#6b7280', fontSize: '14px', margin: '0' }}>Sin cambios aún.</p>
                  ) : (
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {history.map((h, idx) => (
                        <div key={h.id} style={{ paddingBottom: idx < history.length - 1 ? '12px' : '0', marginBottom: idx < history.length - 1 ? '12px' : '0', borderBottom: idx < history.length - 1 ? '1px solid #e5e7eb' : 'none' }}>
                          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#003d9b', flexShrink: 0, marginTop: '2px' }}>check_circle</span>
                            <div style={{ flex: 1 }}>
                              <p style={{ fontWeight: '700', fontSize: '14px', color: '#1f2937', margin: '0' }}>{h.accion}</p>
                              {h.detalle && <p style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px', margin: '0' }}>{h.detalle}</p>}
                              <p style={{ fontSize: '11px', color: '#9ca3af', marginTop: '6px', margin: '0' }}>{formatDate(h.created_at)}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="modal-footer" style={{ borderTop: '2px solid #e5e7eb' }}>
              {selectedPqr.estado === 'resuelta' && (
                <button className="btn btn-primary" onClick={() => handleCerrar(selectedPqr.id)} style={{ fontWeight: '600' }}>
                  Cerrar solicitud
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
                onFileChange={handleViewerFileChange}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
