import { useEffect, useMemo, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { catalogService } from '../services/catalogService';
import { pqrService } from '../services/pqrService';

export function RegistroPQR() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [areas, setAreas] = useState<Array<{ id: string; nombre: string }>>([]);

  const [formData, setFormData] = useState({
    tipo: '',
    area_id: '',
    titulo: '',
    descripcion: '',
  });

  const [adjuntos, setAdjuntos] = useState<File[]>([]);

  useEffect(() => {
    let isMounted = true;
    const loadCatalogs = async () => {
      try {
        const areasData = await catalogService.getAreas();
        if (!isMounted) return;
        setAreas(areasData.map((item) => ({ id: item.id, nombre: item.nombre })));
      } catch {
        if (isMounted) setAreas([]);
      }
    };
    loadCatalogs();
    return () => { isMounted = false; };
  }, []);

  const steps = [
    { num: 1, label: 'Tipo' },
    { num: 2, label: 'Detalles' },
    { num: 3, label: 'Confirmacion' },
  ];

  const tipos = [
    { value: 'peticion', label: 'Peticion', icon: 'edit_note', color: '#059669', bg: '#d1fae5', desc: 'Solicitud formal de informacion o servicio' },
    { value: 'queja', label: 'Queja', icon: 'sentiment_dissatisfied', color: '#dc2626', bg: '#fee2e2', desc: 'Expresion de inconformidad por un servicio' },
    { value: 'reclamo', label: 'Reclamo', icon: 'warning', color: '#d97706', bg: '#fef3c7', desc: 'Protesta formal por incumplimiento' },
  ];

  const currentUserId = useMemo(() => {
    const id = Number(user?.id);
    return Number.isFinite(id) ? id : null;
  }, [user?.id]);

  const canContinue = useMemo(() => {
    if (step === 1) return Boolean(formData.tipo && formData.area_id);
    if (step === 2) return Boolean(formData.titulo.trim() && formData.descripcion.trim().length >= 10);
    return true;
  }, [formData, step]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAdjuntos([...adjuntos, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAdjuntos(adjuntos.filter((_, i) => i !== index));
  };

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
        area_id: Number(formData.area_id),
        titulo: formData.titulo.trim(),
        descripcion: formData.descripcion.trim(),
        estado: 'pendiente',
        usuario_id: currentUserId,
      });

      setCreatedId(created.id);
      navigate('/mis-pqrs');
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
        <h1 className="page-title">Nueva PQR</h1>
        <p className="page-subtitle">Registre su solicitud, queja o reclamo</p>
      </div>

      <div className="card animate-fade-in" style={{ padding: '32px' }}>
        <div className="registro-steps">
          {steps.map((s, i) => (
            <div key={s.num} className="registro-step">
              <div style={{
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
              }}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span className="registro-step-label" style={{ color: step >= s.num ? '#003d9b' : '#525f73' }}>{s.label}</span>
              {i < steps.length - 1 && <div className="registro-step-separator" />}
            </div>
          ))}
        </div>

        <div style={{ minHeight: '300px', marginTop: '24px' }}>
          {step === 1 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Seleccione el tipo de solicitud</h3>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px' }}>¿Que tipo de tramite desea realizar?</p>
              
              <div className="registro-types-grid">
                {tipos.map((tipo) => (
                  <button
                    key={tipo.value}
                    onClick={() => setFormData({ ...formData, tipo: tipo.value })}
                    style={{
                      padding: '24px',
                      borderRadius: '16px',
                      border: `3px solid ${formData.tipo === tipo.value ? tipo.color : '#e5e7eb'}`,
                      background: formData.tipo === tipo.value ? tipo.bg : '#fff',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                      boxShadow: formData.tipo === tipo.value ? '0 16px 28px -24px rgba(30,100,200,0.6)' : 'none',
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '40px', color: tipo.color, marginBottom: '12px' }}>{tipo.icon}</span>
                    <p style={{ fontWeight: '700', fontSize: '18px', marginBottom: '4px', color: tipo.color }}>{tipo.label}</p>
                    <p style={{ fontSize: '13px', color: '#525f73' }}>{tipo.desc}</p>
                  </button>
                ))}
              </div>

              <div style={{ marginTop: '24px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Area responsable</label>
                <select className="select" value={formData.area_id} onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}>
                  <option value="">Seleccione el area</option>
                  {areas.map((item) => (
                    <option key={item.id} value={item.id}>{item.nombre}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Detalles de la solicitud</h3>
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
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Descripción detallada *</label>
                  <textarea
                    className="input"
                    rows={5}
                    placeholder="Describa su solicitud en detalle..."
                    value={formData.descripcion}
                    onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                    style={{ resize: 'vertical' }}
                  />
                  <p style={{ fontSize: '12px', color: '#525f73', marginTop: '8px' }}>{formData.descripcion.length} caracteres</p>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Adjuntos (opcional)</label>
                  <div style={{ border: '2px dashed #e5e7eb', borderRadius: '12px', padding: '20px', textAlign: 'center', cursor: 'pointer' }} onClick={() => fileInputRef.current?.click()}>
                    <span className="material-symbols-outlined" style={{ fontSize: '40px', color: '#9ca3af' }}>cloud_upload</span>
                    <p style={{ marginTop: '8px', color: '#6b7280' }}>Haga clic para seleccionar archivos o imagenes</p>
                    <p style={{ fontSize: '12px', color: '#9ca3af' }}>PNG, JPG, PDF hasta 10MB</p>
                    <input ref={fileInputRef} type="file" multiple accept="image/*,.pdf" style={{ display: 'none' }} onChange={handleFileChange} />
                  </div>
                  {adjuntos.length > 0 && (
                    <div style={{ marginTop: '12px' }}>
                      {adjuntos.map((file, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#f3f4f6', borderRadius: '8px', marginBottom: '8px' }}>
                          <span style={{ fontSize: '13px' }}>{file.name}</span>
                          <button type="button" onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>close</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>Confirmación</h3>
              <div style={{ background: 'linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%)', borderRadius: '16px', padding: '24px', border: '1px solid #dde9ff' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Tipo</p>
                    <span className="badge badge-primary" style={{ textTransform: 'capitalize', background: tipos.find(t => t.value === formData.tipo)?.bg, color: tipos.find(t => t.value === formData.tipo)?.color }}>
                      {tipos.find(t => t.value === formData.tipo)?.label || '-'}
                    </span>
                  </div>
                  <div>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Area</p>
                    <p style={{ fontWeight: '600' }}>{areas.find(a => a.id === formData.area_id)?.nombre || '-'}</p>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Titulo</p>
                    <p style={{ fontWeight: '600' }}>{formData.titulo || '-'}</p>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Descripción</p>
                    <p>{formData.descripcion || '-'}</p>
                  </div>
                  {adjuntos.length > 0 && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Archivos adjuntos</p>
                      <p style={{ fontWeight: '600' }}>{adjuntos.length} archivo(s)</p>
                    </div>
                  )}
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
          {step < 3 ? (
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
