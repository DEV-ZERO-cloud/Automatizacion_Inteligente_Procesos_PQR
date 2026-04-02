import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { catalogService } from '../services/catalogService';
import { pqrService } from '../services/pqrService';

export function RegistroPQR() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [areas, setAreas] = useState<Array<{ id: string; nombre: string }>>([]);
  const [categories, setCategories] = useState<Array<{ id: string; nombre: string }>>([]);
  const [priorities, setPriorities] = useState<Array<{ id: string; nombre: string }>>([]);

  const [formData, setFormData] = useState({
    tipo: '',
    categoria: '',
    prioridad: '',
    area_id: '',
    titulo: '',
    descripcion: '',
  });

  useEffect(() => {
    let isMounted = true;

    const loadCatalogs = async () => {
      try {
        const [areasData, categoriesData, prioritiesData] = await Promise.all([
          catalogService.getAreas(),
          catalogService.getCategories(),
          catalogService.getPriorities(),
        ]);

        if (!isMounted) {
          return;
        }

        setAreas(areasData.map((item) => ({ id: item.id, nombre: item.nombre })));
        setCategories(categoriesData.map((item) => ({ id: item.id, nombre: item.nombre })));
        setPriorities(prioritiesData.map((item) => ({ id: item.id, nombre: item.nombre })));
      } catch {
        if (isMounted) {
          setAreas([]);
          setCategories([]);
          setPriorities([]);
        }
      }
    };

    loadCatalogs();
    return () => {
      isMounted = false;
    };
  }, []);

  const steps = [
    { num: 1, label: 'Solicitante' },
    { num: 2, label: 'Clasificacion Inicial' },
    { num: 3, label: 'Descripcion' },
    { num: 4, label: 'Confirmacion' },
  ];

  const tipos = [
    { value: 'peticion', label: 'Peticion', icon: 'handshake', desc: 'Solicitud formal' },
    { value: 'queja', label: 'Queja', icon: 'sentiment_dissatisfied', desc: 'Inconformidad' },
    { value: 'reclamo', label: 'Reclamo', icon: 'report', desc: 'Protesta formal' },
  ];

  const currentUserId = useMemo(() => {
    const id = Number(user?.id);
    return Number.isFinite(id) ? id : null;
  }, [user?.id]);

  const canContinue = useMemo(() => {
    if (step === 1) {
      return Boolean(currentUserId);
    }
    if (step === 2) {
      return Boolean(formData.tipo && formData.categoria && formData.prioridad && formData.area_id);
    }
    if (step === 3) {
      return Boolean(formData.titulo.trim() && formData.descripcion.trim().length >= 20);
    }
    return true;
  }, [currentUserId, formData, step]);

  const handleSubmit = async () => {
    if (!currentUserId) {
      setError('No se pudo identificar el usuario autenticado.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const created = await pqrService.create({
        tipo: formData.tipo,
        categoria: formData.categoria,
        prioridad: formData.prioridad,
        area_id: Number(formData.area_id),
        titulo: formData.titulo.trim(),
        descripcion: formData.descripcion.trim(),
        estado: 'pendiente',
        usuario_id: currentUserId,
      });

      setCreatedId(created.id);
      navigate('/bandeja-entrada');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'No fue posible registrar la solicitud.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Registro de PQR</h1>
        <p className="page-subtitle">Diligencie el formulario para registrar su solicitud</p>
      </div>

      <div className="card animate-fade-in" style={{ padding: '32px' }}>
        <div className="registro-steps">
          {steps.map((s, i) => (
            <div key={s.num} className="registro-step">
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: step >= s.num ? '#003d9b' : '#f2f4f7',
                  color: step >= s.num ? '#fff' : '#525f73',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '700',
                  fontSize: '14px',
                  transition: 'all 0.3s',
                }}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              <span className="registro-step-label" style={{ color: step >= s.num ? '#003d9b' : '#525f73' }}>{s.label}</span>
              {i < steps.length - 1 && <div className="registro-step-separator" />}
            </div>
          ))}
        </div>

        <div style={{ minHeight: '280px' }}>
          {step === 1 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Datos del Solicitante</h3>
              <div style={{ display: 'grid', gap: '20px' }}>
                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                  <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Nombre</p>
                  <p style={{ fontWeight: '700' }}>{user?.full_name || user?.username || '-'}</p>
                </div>
                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                  <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Correo</p>
                  <p style={{ fontWeight: '700' }}>{user?.email || '-'}</p>
                </div>
                <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
                  <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '6px' }}>Rol</p>
                  <p style={{ fontWeight: '700', textTransform: 'capitalize' }}>{user?.rol_id || '-'}</p>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Clasificacion Inicial</h3>
              <div className="registro-types-grid">
                {tipos.map((tipo) => (
                  <button
                    key={tipo.value}
                    onClick={() => setFormData({ ...formData, tipo: tipo.value })}
                    style={{
                      padding: '24px',
                      borderRadius: '16px',
                      border: `2px solid ${formData.tipo === tipo.value ? '#003d9b' : '#e6e8eb'}`,
                      background: formData.tipo === tipo.value ? '#dae2ff' : '#fff',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '32px', color: '#003d9b', marginBottom: '12px' }}>{tipo.icon}</span>
                    <p style={{ fontWeight: '700', marginBottom: '4px' }}>{tipo.label}</p>
                    <p style={{ fontSize: '12px', color: '#525f73' }}>{tipo.desc}</p>
                  </button>
                ))}
              </div>

              <div style={{ display: 'grid', gap: '16px', marginTop: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Categoria</label>
                  <select className="select" value={formData.categoria} onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}>
                    <option value="">Seleccione una categoria</option>
                    {categories.map((item) => (
                      <option key={item.id} value={item.nombre}>{item.nombre}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Prioridad</label>
                  <select className="select" value={formData.prioridad} onChange={(e) => setFormData({ ...formData, prioridad: e.target.value })}>
                    <option value="">Seleccione una prioridad</option>
                    {priorities.map((item) => (
                      <option key={item.id} value={item.nombre}>{item.nombre}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Area responsable</label>
                  <select className="select" value={formData.area_id} onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}>
                    <option value="">Seleccione un area</option>
                    {areas.map((item) => (
                      <option key={item.id} value={item.id}>{item.nombre}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Descripcion de la Solicitud</h3>
              <div style={{ display: 'grid', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Titulo *</label>
                  <input
                    className="input"
                    placeholder="Resumen breve de su solicitud"
                    value={formData.titulo}
                    onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Descripcion detallada *</label>
                  <textarea
                    className="input"
                    rows={5}
                    placeholder="Describa su solicitud en detalle (minimo 20 caracteres)"
                    value={formData.descripcion}
                    onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                    style={{ resize: 'vertical' }}
                  />
                  <p style={{ fontSize: '12px', color: '#525f73', marginTop: '8px' }}>{formData.descripcion.length} caracteres</p>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Confirmacion</h3>
              <div style={{ background: '#f8fafc', borderRadius: '16px', padding: '24px' }}>
                <div className="registro-confirm-grid">
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Solicitante</p>
                    <p style={{ fontWeight: '600' }}>{user?.full_name || user?.username || '-'}</p>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Tipo</p>
                    <span className="badge badge-primary" style={{ textTransform: 'capitalize' }}>{formData.tipo || '-'}</span>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Categoria</p>
                    <p style={{ fontWeight: '600' }}>{formData.categoria || '-'}</p>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Prioridad</p>
                    <p style={{ fontWeight: '600' }}>{formData.prioridad || '-'}</p>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Titulo</p>
                    <p style={{ fontWeight: '600' }}>{formData.titulo || '-'}</p>
                  </div>
                </div>
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e6e8eb' }}>
                  <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Descripcion</p>
                  <p>{formData.descripcion || '-'}</p>
                </div>
              </div>
              {createdId && (
                <p style={{ color: '#047857', fontSize: '13px', marginTop: '16px', fontWeight: 600 }}>PQR creada exitosamente con ID #{createdId}.</p>
              )}
            </div>
          )}
        </div>

        {error && (
          <div style={{ marginTop: '16px', background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: '10px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '32px', paddingTop: '24px', borderTop: '1px solid #f2f4f7' }}>
          {step > 1 ? (
            <button className="btn btn-secondary" onClick={() => setStep(step - 1)} disabled={submitting}>Anterior</button>
          ) : (
            <div />
          )}
          {step < 4 ? (
            <button className="btn btn-primary" onClick={() => setStep(step + 1)} disabled={!canContinue || submitting}>Siguiente</button>
          ) : (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !canContinue}>
              {submitting ? 'Enviando...' : 'Enviar Solicitud'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
