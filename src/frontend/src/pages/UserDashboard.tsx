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
  const [showCrearModal, setShowCrearModal] = useState(false);
  const [showRespuestasModal, setShowRespuestasModal] = useState(false);

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

      // Close modal after success
      setTimeout(() => {
        setShowCrearModal(false);
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
        run: () => setShowCrearModal(true),
      });
    }

    return actions.slice(0, 2);
  }, [pqrPendienteMasAntigua, sortedByDateDesc]);

  const priorityCases = useMemo(() => {
    return sortedByDateDesc
      .filter((p) => ['urgente', 'alta'].includes((p.prioridad || '').toLowerCase()))
      .slice(0, 3);
  }, [sortedByDateDesc]);

  const userInitials = (user?.full_name || 'U').split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(160deg, #f6f9ff 0%, #eef3fb 100%)' }}>
      {/* Topbar compacta */}
      <div style={{
        background: 'linear-gradient(135deg, #0b3b7a 0%, #1553a1 60%, #0f766e 100%)',
        color: '#fff',
        padding: '0 28px',
        height: '60px',
        boxShadow: '0 2px 16px rgba(11,59,122,0.35)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(255,255,255,0.18)', border: '1px solid rgba(255,255,255,0.28)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#fff' }}>inbox</span>
          </div>
          <div>
            <p style={{ margin: 0, fontFamily: 'Sora, sans-serif', fontWeight: 700, fontSize: '15px', color: '#fff', lineHeight: 1.1 }}>Sistema PQR</p>
            <p style={{ margin: 0, fontSize: '10px', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>Portal ciudadano</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ textAlign: 'right' }}>
            <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: '#fff' }}>{user?.full_name || 'Usuario'}</p>
            <p style={{ margin: 0, fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>Ciudadano</p>
          </div>
          <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255,255,255,0.22)', border: '1.5px solid rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '14px', color: '#fff' }}>
            {userInitials}
          </div>
          <button
            title="Cerrar sesión"
            onClick={() => { useAuthStore.getState().logout(); window.location.href = '/login'; }}
            style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.28)', borderRadius: '8px', color: '#fff', width: '36px', height: '36px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s' }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>logout</span>
          </button>
        </div>
      </div>

      {/* Hero saludo */}
      <div style={{ background: 'linear-gradient(90deg, #ecf4ff 0%, #f7fbff 80%, #ecfdf5 100%)', borderBottom: '1px solid #dbeafe', padding: '20px 28px 18px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <h1 style={{ margin: 0, fontFamily: 'Sora, sans-serif', fontSize: '22px', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.3px' }}>Bienvenido de vuelta, <span style={{ color: '#1553a1' }}>{(user?.full_name || 'Usuario').split(' ')[0]}</span> 👋</h1>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>Aquí tienes el estado actual de todas tus solicitudes</p>
        </div>
      </div>

      {/* Stats grid */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px 28px 0' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
          {[
            { icon: 'folder_open', label: 'Total Solicitudes', value: pqrs.length, color: '#003d9b', bg: '#dbeafe', progress: null },
            { icon: 'pending', label: 'En atención', value: pendientes + proceso, color: '#d97706', bg: '#fef3c7', progress: pqrs.length ? Math.round(((pendientes + proceso) / pqrs.length) * 100) : 0 },
            { icon: 'check_circle', label: 'Resueltas', value: totalResueltasOCerradas, color: '#059669', bg: '#d1fae5', progress: tasaResolucion },
            { icon: 'speed', label: 'Tasa de resolución', value: `${tasaResolucion}%`, color: '#0f766e', bg: '#ccfbf1', progress: tasaResolucion },
          ].map((stat, i) => (
            <div key={i} className="card" style={{ padding: '18px 20px', display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: stat.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span className="material-symbols-outlined" style={{ fontSize: '22px', color: stat.color }}>{stat.icon}</span>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{stat.label}</p>
                <p style={{ margin: '4px 0 0', fontSize: '26px', fontWeight: 800, color: stat.color, lineHeight: 1 }}>{stat.value}</p>
                {stat.progress !== null && (
                  <div style={{ marginTop: '8px' }}>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${stat.progress}%`, background: stat.color }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginTop: '16px' }}>
          {/* Card acciones recomendadas */}
          <div className="card" style={{ padding: '20px 22px', background: 'linear-gradient(135deg, #f0f5ff 0%, #f8fbff 100%)', border: '1px solid #dbeafe' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="material-symbols-outlined" style={{ color: '#1553a1', fontSize: '20px' }}>tips_and_updates</span>
                <p style={{ fontSize: '12px', color: '#1553a1', fontWeight: 700, textTransform: 'uppercase', margin: 0, letterSpacing: '0.5px' }}>Acción recomendada</p>
              </div>
              <span className="badge badge-primary" style={{ fontSize: '10px' }}>IA</span>
            </div>
            <div style={{ display: 'grid', gap: '10px' }}>
              {recommendedActions.map((action) => (
                <div key={action.key} style={{ border: '1px solid #bfdbfe', borderRadius: '12px', padding: '14px 16px', background: '#fff', boxShadow: '0 1px 4px rgba(0,61,155,0.06)' }}>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span className="material-symbols-outlined" style={{ color: '#1553a1', fontSize: '20px' }}>{action.icon}</span>
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>{action.title}</p>
                      <p style={{ margin: '4px 0 10px', fontSize: '12px', color: '#64748b', lineHeight: 1.5 }}>{action.description}</p>
                      <button className="btn btn-primary btn-sm" onClick={action.run} style={{ fontSize: '12px' }}>{action.cta}</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card casos prioritarios con timeline */}
          <div className="card" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="material-symbols-outlined" style={{ color: '#dc2626', fontSize: '20px' }}>priority_high</span>
                <p style={{ fontSize: '12px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', margin: 0, letterSpacing: '0.5px' }}>Casos prioritarios</p>
              </div>
              {priorityCases.length > 0 && <span className="badge badge-danger">{priorityCases.length} activos</span>}
            </div>
            {priorityCases.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '16px 0', color: '#64748b' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '36px', color: '#d1d5db' }}>check_circle</span>
                <p style={{ margin: '8px 0 0', fontSize: '13px' }}>Sin casos urgentes actualmente</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '0' }}>
                {priorityCases.map((p, idx) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleVerDetalle(p)}
                    style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '12px 0', borderBottom: idx < priorityCases.length - 1 ? '1px solid #f1f5f9' : 'none', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%', borderBottomStyle: 'solid', borderBottomWidth: idx < priorityCases.length - 1 ? '1px' : '0', borderBottomColor: '#f1f5f9' }}
                  >
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#dc2626', flexShrink: 0, marginTop: '5px' }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>#{p.id} · {p.titulo}</p>
                      <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>{p.tipo} · {formatDate(p.created_at)}</p>
                    </div>
                    <span className="badge badge-warning" style={{ textTransform: 'capitalize', flexShrink: 0 }}>{p.prioridad || 'alta'}</span>
                  </button>
                ))}
              </div>
            )}
            {pqrMasReciente && (
              <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#64748b' }}>history</span>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Última actividad: <strong style={{ color: '#1e293b' }}>#{pqrMasReciente.id}</strong></p>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => handleVerDetalle(pqrMasReciente)} style={{ fontSize: '12px' }}>Ver</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Action bar */}
      <div style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', padding: '12px 28px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#1553a1' }}>inbox</span>
            <p style={{ margin: 0, fontWeight: 700, fontSize: '15px', color: '#0f172a' }}>Mis Solicitudes</p>
            <span style={{ background: '#dbeafe', color: '#003d9b', padding: '2px 9px', borderRadius: '10px', fontSize: '12px', fontWeight: 700 }}>{pqrs.length}</span>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setShowRespuestasModal(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '7px', fontWeight: 600 }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '17px' }}>mail_outline</span>
              Respuestas
              {resueltas.length > 0 && (
                <span style={{ background: '#059669', color: '#fff', padding: '1px 7px', borderRadius: '9px', fontSize: '11px', fontWeight: 700 }}>{resueltas.length}</span>
              )}
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => { setCreateStep(1); setFormData({ tipo: '', titulo: '', descripcion: '' }); setAdjuntos([]); setCreateError(''); setCreateSuccess(''); setShowCrearModal(true); }}
              style={{ display: 'flex', alignItems: 'center', gap: '7px', fontWeight: 600 }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '17px' }}>add_circle</span>
              Nueva Solicitud
            </button>
          </div>
        </div>
      </div>

      {/* Content — only lista */}
      <div style={{ padding: '28px 28px', maxWidth: '1400px', margin: '0 auto' }}>

        {/* Lista */}
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
              <button className="btn btn-primary" onClick={() => { setCreateStep(1); setFormData({ tipo: '', titulo: '', descripcion: '' }); setAdjuntos([]); setCreateError(''); setCreateSuccess(''); setShowCrearModal(true); }} style={{ fontSize: '14px', fontWeight: '600' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add_circle</span>
                Nueva solicitud
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
                    <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                      <th style={{ fontWeight: '700', color: '#475569', fontSize: '11px', letterSpacing: '0.5px' }}>ID</th>
                      <th style={{ fontWeight: '700', color: '#475569', fontSize: '11px', letterSpacing: '0.5px' }}>Asunto</th>
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

      </div>

      {/* ── Modal: Nueva Solicitud ── */}
      {showCrearModal && (
        <div className="modal-overlay" onClick={() => setShowCrearModal(false)} style={{ zIndex: 250 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '680px', width: '95%', padding: 0, maxHeight: '90vh', overflowY: 'auto', borderRadius: '20px' }}>
            {/* Modal header */}
            <div style={{ padding: '24px 28px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(90deg, #f0f5ff 0%, #f8fbff 100%)', borderRadius: '20px 20px 0 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span className="material-symbols-outlined" style={{ color: '#003d9b', fontSize: '22px' }}>edit_note</span>
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>Nueva Solicitud</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Completa los campos para registrar tu solicitud</p>
                </div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowCrearModal(false)} style={{ borderRadius: '8px' }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            {/* Modal body */}
            <div style={{ padding: '28px' }}>
              {/* Step indicator */}
              <div style={{ display: 'flex', gap: '20px', marginBottom: '28px' }}>
                {([1, 2] as const).map((step) => (
                  <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: createStep >= step ? 'linear-gradient(135deg, #003d9b 0%, #0052cc 100%)' : '#e5e7eb', color: createStep >= step ? '#fff' : '#9ca3af', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '15px', fontWeight: 700, boxShadow: createStep >= step ? '0 4px 12px rgba(0,61,155,0.3)' : 'none' }}>
                      {createStep > step ? '✓' : step}
                    </div>
                    <span style={{ color: createStep >= step ? '#003d9b' : '#9ca3af', fontWeight: 600, fontSize: '14px' }}>
                      {step === 1 ? 'Tipo y Asunto' : 'Confirmación'}
                    </span>
                    {step === 1 && <div style={{ width: '32px', height: '2px', background: createStep >= 2 ? '#003d9b' : '#e5e7eb', borderRadius: '2px' }} />}
                  </div>
                ))}
              </div>

              {createSuccess && (
                <div style={{ background: '#dcfce7', color: '#166534', padding: '14px 16px', borderRadius: '12px', marginBottom: '20px', fontSize: '14px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>check_circle</span>
                  {createSuccess}
                </div>
              )}
              {createError && (
                <div style={{ background: '#fee2e2', color: '#991b1b', padding: '14px 16px', borderRadius: '12px', marginBottom: '20px', fontSize: '14px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>error</span>
                  {createError}
                </div>
              )}

              {createStep === 1 && (
                <div style={{ animation: 'fadeIn 0.3s ease' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '14px', color: '#1f2937', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Tipo de solicitud</h3>
                  <div style={{ display: 'grid', gap: '10px', marginBottom: '24px' }}>
                    {tipos.map((tipo) => (
                      <button
                        key={tipo.value}
                        onClick={() => setFormData({ ...formData, tipo: tipo.value })}
                        style={{ padding: '16px', borderRadius: '12px', border: `2px solid ${formData.tipo === tipo.value ? tipo.color : '#e5e7eb'}`, background: formData.tipo === tipo.value ? tipo.bg : '#fff', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '28px', color: tipo.color }}>{tipo.icon}</span>
                          <div>
                            <p style={{ fontWeight: 700, color: tipo.color, margin: 0, fontSize: '15px' }}>{tipo.label}</p>
                            <p style={{ fontSize: '12px', color: '#6b7280', margin: '2px 0 0' }}>{tipo.desc}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Asunto *</label>
                    <input className="input" placeholder="Resumen breve de tu solicitud" value={formData.titulo} onChange={(e) => setFormData({ ...formData, titulo: e.target.value })} />
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Descripción * <span style={{ fontWeight: 400, color: '#94a3b8', textTransform: 'none' }}>({formData.descripcion.length}/10 mín.)</span></label>
                    <textarea className="input" rows={4} placeholder="Cuéntanos los detalles de tu solicitud..." value={formData.descripcion} onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })} style={{ resize: 'vertical' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Adjuntos (opcional)</label>
                    <div style={{ border: '2px dashed #d1d5db', borderRadius: '12px', padding: '24px', textAlign: 'center', cursor: 'pointer', background: '#f9fafb', transition: 'all 0.2s' }} onClick={() => fileInputRef.current?.click()}>
                      <span className="material-symbols-outlined" style={{ fontSize: '36px', color: '#9ca3af' }}>cloud_upload</span>
                      <p style={{ marginTop: '6px', color: '#6b7280', fontSize: '13px', fontWeight: 500 }}>Haz clic para adjuntar archivos</p>
                      <p style={{ fontSize: '11px', color: '#9ca3af', margin: '2px 0 0' }}>PNG, JPG, PDF (máx. 10MB c/u)</p>
                      <input ref={fileInputRef} type="file" multiple accept="image/*,.pdf" style={{ display: 'none' }} onChange={handleFileChange} />
                    </div>
                    {adjuntos.length > 0 && (
                      <div style={{ marginTop: '10px', display: 'grid', gap: '6px' }}>
                        {adjuntos.map((file, i) => (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: '#f3f4f6', borderRadius: '8px' }}>
                            <span style={{ fontSize: '13px', fontWeight: 500 }}>{file.name}</span>
                            <button type="button" onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}>
                              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>close</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {createStep === 2 && (
                <div style={{ animation: 'fadeIn 0.3s ease' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', color: '#1f2937', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Revisa tu solicitud</h3>
                  <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '20px', display: 'grid', gap: '16px' }}>
                    <div style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '14px' }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: 700, textTransform: 'uppercase', margin: '0 0 6px' }}>Tipo</p>
                      <span style={{ background: tipos.find(t => t.value === formData.tipo)?.bg, color: tipos.find(t => t.value === formData.tipo)?.color, padding: '6px 12px', borderRadius: '8px', fontSize: '13px', fontWeight: 600 }}>
                        {tipos.find(t => t.value === formData.tipo)?.label || '-'}
                      </span>
                    </div>
                    <div style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '14px' }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: 700, textTransform: 'uppercase', margin: '0 0 6px' }}>Asunto</p>
                      <p style={{ fontWeight: 600, margin: 0, fontSize: '15px', color: '#1f2937' }}>{formData.titulo || '-'}</p>
                    </div>
                    <div style={{ borderBottom: adjuntos.length > 0 ? '1px solid #e5e7eb' : 'none', paddingBottom: adjuntos.length > 0 ? '14px' : 0 }}>
                      <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: 700, textTransform: 'uppercase', margin: '0 0 6px' }}>Descripción</p>
                      <p style={{ fontSize: '14px', lineHeight: 1.6, color: '#525f73', margin: 0 }}>{formData.descripcion || '-'}</p>
                    </div>
                    {adjuntos.length > 0 && (
                      <div>
                        <p style={{ fontSize: '11px', color: '#6b7280', fontWeight: 700, textTransform: 'uppercase', margin: '0 0 6px' }}>Adjuntos</p>
                        <p style={{ fontWeight: 600, margin: 0, fontSize: '14px', color: '#059669' }}>{adjuntos.length} archivo(s) listos para enviar</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '28px', justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setShowCrearModal(false)} disabled={submitting}>Cancelar</button>
                {createStep > 1 && (
                  <button className="btn btn-secondary" onClick={() => setCreateStep(1)} disabled={submitting}>← Atrás</button>
                )}
                {createStep === 1 && (
                  <button className="btn btn-primary" onClick={() => { if (!formData.tipo || !formData.titulo.trim() || formData.descripcion.trim().length < 10) { setCreateError('Completa tipo, asunto y una descripción mínima de 10 caracteres.'); return; } setCreateError(''); setCreateStep(2); }} disabled={submitting}>Siguiente →</button>
                )}
                {createStep === 2 && (
                  <button className="btn btn-primary" onClick={handleCreateSubmit} disabled={submitting || !canContinue}>{submitting ? 'Enviando...' : 'Enviar Solicitud'}</button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Respuestas ── */}
      {showRespuestasModal && (
        <div className="modal-overlay" onClick={() => setShowRespuestasModal(false)} style={{ zIndex: 250 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px', width: '95%', padding: 0, maxHeight: '90vh', overflowY: 'auto', borderRadius: '20px' }}>
            {/* Header */}
            <div style={{ padding: '24px 28px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(90deg, #ecfdf5 0%, #f8fbff 100%)', borderRadius: '20px 20px 0 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: '#d1fae5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span className="material-symbols-outlined" style={{ color: '#059669', fontSize: '22px' }}>mail</span>
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>Respuestas</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>{resueltas.length > 0 ? `${resueltas.length} solicitud(es) respondida(s)` : 'Sin respuestas aún'}</p>
                </div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowRespuestasModal(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            {/* Body */}
            <div style={{ padding: '24px 28px' }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '40px', color: '#d1d5db' }}>hourglass_empty</span>
                  <p style={{ color: '#6b7280', marginTop: '12px' }}>Cargando respuestas...</p>
                </div>
              ) : resueltas.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '48px 20px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '52px', color: '#d1d5db' }}>mail_outline</span>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#1f2937', margin: '12px 0 8px' }}>Aún no tienes respuestas</h3>
                  <p style={{ color: '#6b7280', fontSize: '14px', margin: 0 }}>Las respuestas aparecerán aquí cuando tus solicitudes sean resueltas</p>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '14px' }}>
                  {resueltas.map((pqr) => (
                    <div key={pqr.id} style={{ background: '#f8fafc', borderRadius: '14px', padding: '20px', border: '1px solid #d1fae5', borderLeft: '4px solid #10b981' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                        <div>
                          <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 4px', color: '#1f2937' }}>Solicitud #{pqr.id}</h3>
                          <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>{pqr.titulo}</p>
                        </div>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '5px 12px', borderRadius: '8px', background: '#dcfce7', color: '#166534', fontSize: '12px', fontWeight: 600, flexShrink: 0 }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>check_circle</span>
                          Resuelto
                        </div>
                      </div>
                      <p style={{ color: '#525f73', margin: '0 0 14px', lineHeight: 1.6, fontSize: '14px' }}>{pqr.descripcion}</p>
                      <button className="btn btn-ghost btn-sm" onClick={() => { setShowRespuestasModal(false); handleVerDetalle(pqr); }} style={{ color: '#003d9b', fontWeight: 600 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
                        Ver detalles y historial
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal for details */}
      {showModal && selectedPqr && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '740px', width: '95%', padding: 0, borderRadius: '20px', maxHeight: '92vh', display: 'flex', flexDirection: 'column' }}>

            {/* Header dinámico según estado */}
            <div style={{
              padding: '24px 28px 20px',
              background: `linear-gradient(135deg, ${estadoColors[selectedPqr.estado]?.bg || '#f8fafc'} 0%, #f8fbff 100%)`,
              borderBottom: `1px solid ${estadoColors[selectedPqr.estado]?.bg || '#e2e8f0'}`,
              borderRadius: '20px 20px 0 0',
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
                    <span style={{ fontFamily: 'Sora, sans-serif', fontSize: '20px', fontWeight: 800, color: '#0f172a' }}>Solicitud #{selectedPqr.id}</span>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      padding: '3px 10px', borderRadius: '20px',
                      background: estadoColors[selectedPqr.estado]?.bg,
                      color: estadoColors[selectedPqr.estado]?.text,
                      fontSize: '12px', fontWeight: 700,
                    }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>{estadoColors[selectedPqr.estado]?.icon}</span>
                      {selectedPqr.estado.replace('_', ' ')}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#334155' }}>{selectedPqr.titulo}</p>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={handleCloseModal} style={{ flexShrink: 0, marginLeft: '12px' }}>
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
              {/* Metadata pills */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '14px' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 11px', borderRadius: '20px', background: 'rgba(255,255,255,0.75)', border: '1px solid #e2e8f0', fontSize: '12px', fontWeight: 600, color: '#475569' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>category</span>{selectedPqr.tipo}
                </div>
                {selectedPqr.categoria && (
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 11px', borderRadius: '20px', background: '#dbeafe', border: '1px solid #bfdbfe', fontSize: '12px', fontWeight: 600, color: '#1d4ed8' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>label</span>{selectedPqr.categoria}
                  </div>
                )}
                {selectedPqr.prioridad && (
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 11px', borderRadius: '20px', background: '#fef3c7', border: '1px solid #fde68a', fontSize: '12px', fontWeight: 600, color: '#92400e' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>flag</span>{selectedPqr.prioridad}
                  </div>
                )}
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 11px', borderRadius: '20px', background: 'rgba(255,255,255,0.75)', border: '1px solid #e2e8f0', fontSize: '12px', fontWeight: 600, color: '#64748b' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>calendar_today</span>{formatDate(selectedPqr.created_at)}
                </div>
              </div>
            </div>
            {/* Scrollable body */}
            <div style={{ overflowY: 'auto', flex: 1 }}>

              {/* Descripción */}
              <div style={{ padding: '20px 28px', borderBottom: '1px solid #f1f5f9' }}>
                <p style={{ margin: '0 0 8px', fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.7px' }}>Descripción</p>
                <p style={{ lineHeight: '1.7', color: '#374151', margin: 0, fontSize: '14px' }}>{selectedPqr.descripcion}</p>
              </div>

              {/* Archivos adjuntos */}
              <div style={{ padding: '20px 28px', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: attachments.length > 0 ? '#dbeafe' : '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '15px', color: attachments.length > 0 ? '#1d4ed8' : '#94a3b8' }}>attach_file</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Archivos adjuntos</p>
                  {!loadingAttachments && (
                    <span style={{ padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: 700, background: attachments.length > 0 ? '#003d9b' : '#e5e7eb', color: attachments.length > 0 ? '#fff' : '#64748b' }}>
                      {attachments.length}
                    </span>
                  )}
                </div>
                {loadingAttachments ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', background: '#f8fafc', borderRadius: '10px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#94a3b8' }}>hourglass_empty</span>
                    <p style={{ margin: 0, fontSize: '13px', color: '#6b7280' }}>Cargando archivos...</p>
                  </div>
                ) : attachments.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px dashed #e2e8f0' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#d1d5db' }}>folder_open</span>
                    <p style={{ margin: 0, fontSize: '13px', color: '#9ca3af' }}>Esta solicitud no tiene archivos adjuntos</p>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {attachments.map((file, idx) => {
                      const isImg = file.tipo?.startsWith('image/');
                      const isPdf = file.tipo === 'application/pdf';
                      const icon = isImg ? 'image' : isPdf ? 'picture_as_pdf' : 'insert_drive_file';
                      const iconColor = isImg ? '#0ea5e9' : isPdf ? '#dc2626' : '#6366f1';
                      const iconBg = isImg ? '#e0f2fe' : isPdf ? '#fee2e2' : '#ede9fe';
                      return (
                        <div key={file.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '11px 14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: iconColor }}>{icon}</span>
                          </div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.nombre}</p>
                            <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#94a3b8' }}>Archivo {idx + 1} de {attachments.length}</p>
                          </div>
                          <button className="btn btn-sm btn-secondary" onClick={() => handlePreviewAttachment(file)} style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>visibility</span>Ver
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Historial de cambios — timeline */}
              <div style={{ padding: '20px 28px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: history.length > 0 ? '#d1fae5' : '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '15px', color: history.length > 0 ? '#059669' : '#94a3b8' }}>history</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Historial de actuaciones</p>
                  {!loadingHistory && (
                    <span style={{ padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: 700, background: history.length > 0 ? '#059669' : '#e5e7eb', color: history.length > 0 ? '#fff' : '#64748b' }}>
                      {history.length}
                    </span>
                  )}
                </div>
                {loadingHistory ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', background: '#f8fafc', borderRadius: '10px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#94a3b8' }}>hourglass_empty</span>
                    <p style={{ margin: 0, fontSize: '13px', color: '#6b7280' }}>Cargando historial...</p>
                  </div>
                ) : history.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px dashed #e2e8f0' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#d1d5db' }}>pending_actions</span>
                    <p style={{ margin: 0, fontSize: '13px', color: '#9ca3af' }}>Esta solicitud aún no tiene actuaciones registradas</p>
                  </div>
                ) : (
                  <div style={{ position: 'relative', paddingLeft: '28px' }}>
                    {/* Línea de tiempo vertical */}
                    <div style={{ position: 'absolute', left: '9px', top: '10px', bottom: '10px', width: '2px', background: 'linear-gradient(180deg, #003d9b 0%, #e2e8f0 100%)', borderRadius: '2px' }} />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {history.map((h, idx) => (
                        <div key={h.id} style={{ position: 'relative', display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                          {/* Dot */}
                          <div style={{
                            position: 'absolute', left: '-23px', top: '8px',
                            width: '16px', height: '16px', borderRadius: '50%',
                            background: idx === 0 ? '#003d9b' : '#fff',
                            border: `2px solid ${idx === 0 ? '#003d9b' : '#d1d5db'}`,
                            zIndex: 1,
                          }} />
                          {/* Card */}
                          <div style={{ flex: 1, background: idx === 0 ? '#f0f5ff' : '#f8fafc', borderRadius: '10px', padding: '11px 14px', border: `1px solid ${idx === 0 ? '#dbeafe' : '#f1f5f9'}` }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                              <p style={{ fontWeight: 700, fontSize: '13px', color: idx === 0 ? '#1553a1' : '#1e293b', margin: 0 }}>{h.accion}</p>
                              <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0, flexShrink: 0, whiteSpace: 'nowrap' }}>{formatDate(h.created_at)}</p>
                            </div>
                            {h.detalle && (
                              <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '5px', marginBottom: 0, lineHeight: 1.5 }}>{h.detalle}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            {/* Footer */}
            <div style={{ padding: '16px 28px', borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0, background: '#f8fafc', borderRadius: '0 0 20px 20px' }}>
              <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
                {!loadingAttachments && !loadingHistory && `${attachments.length} archivo(s) · ${history.length} actuación(es)`}
              </p>
              <div style={{ display: 'flex', gap: '10px' }}>
                {selectedPqr.estado === 'resuelta' && (
                  <button className="btn btn-primary" onClick={() => handleCerrar(selectedPqr.id)} style={{ fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_circle</span>
                    Cerrar solicitud
                  </button>
                )}
                <button className="btn btn-secondary" onClick={handleCloseModal} style={{ fontSize: '13px' }}>Cerrar</button>
              </div>
            </div>

          </div>
        </div>
      )}

      {showViewer && attachments.length > 0 && (
        <div className="modal-overlay" onClick={() => setShowViewer(false)} style={{ zIndex: 300 }}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '1000px', width: '80%', maxHeight: '80vh', margin: '20px' }}>
            <div className="modal-header" style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Vista previa: {attachments[currentFileIndex]?.nombre}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowViewer(false)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="modal-body" style={{ padding: 0, height: 'calc(80vh - 80px)', overflow: 'hidden' }}>
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
