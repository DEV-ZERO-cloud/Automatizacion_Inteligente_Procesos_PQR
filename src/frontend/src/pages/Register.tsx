import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuthStore } from '../stores/authStore';

export function Register() {
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const [form, setForm] = useState({
    identificacion: '',
    nombre: '',
    correo: '',
    telefono: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setField = (key: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.identificacion || !form.nombre || !form.correo || !form.password) {
      setError('Completa los campos obligatorios.');
      return;
    }
    if (!/^\d{5,20}$/.test(form.identificacion)) {
      setError('La identificación debe contener solo números (5 a 20 dígitos).');
      return;
    }
    if (form.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.register({
        identificacion: Number(form.identificacion),
        nombre: form.nombre.trim(),
        correo: form.correo.trim().toLowerCase(),
        telefono: form.telefono.trim() || undefined,
        password: form.password,
      });
      login(response.user, response.access_token);
      navigate('/');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || 'No fue posible completar el registro.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(160deg, #0b3b7a 0%, #1f2937 60%, #0f766e 100%)', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '560px' }}>
        <div className="card animate-fade-in" style={{ padding: '36px' }}>
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div className="stat-icon" style={{ width: '60px', height: '60px', margin: '0 auto 14px', background: '#0b3b7a' }}>
              <span className="material-symbols-outlined text-white" style={{ fontSize: '30px' }}>person_add</span>
            </div>
            <h1 style={{ fontSize: '26px', fontWeight: 800, marginBottom: '6px' }}>Crear cuenta</h1>
            <p style={{ color: '#525f73', fontSize: '14px' }}>Acceso al portal de gestión PQR</p>
          </div>

          {error ? (
            <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: '10px', marginBottom: '18px', fontSize: '14px', fontWeight: 500 }}>
              {error}
            </div>
          ) : null}

          <form onSubmit={handleSubmit}>
            <div className="modal-grid-two" style={{ marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Identificación
                </label>
                <input className="input" value={form.identificacion} onChange={(e) => setField('identificacion', e.target.value)} placeholder="1000123456" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Nombre completo
                </label>
                <input className="input" value={form.nombre} onChange={(e) => setField('nombre', e.target.value)} placeholder="Juan Perez" />
              </div>
            </div>

            <div className="modal-grid-two" style={{ marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Correo
                </label>
                <input type="email" className="input" value={form.correo} onChange={(e) => setField('correo', e.target.value)} placeholder="correo@ejemplo.com" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Teléfono
                </label>
                <input className="input" value={form.telefono} onChange={(e) => setField('telefono', e.target.value)} placeholder="3001234567" />
              </div>
            </div>

            <div className="modal-grid-two" style={{ marginBottom: '18px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Contraseña
                </label>
                <input type="password" className="input" value={form.password} onChange={(e) => setField('password', e.target.value)} placeholder="Minimo 8 caracteres" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                  Confirmar contraseña
                </label>
                <input type="password" className="input" value={form.confirmPassword} onChange={(e) => setField('confirmPassword', e.target.value)} placeholder="Repite tu contraseña" />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '6px' }} disabled={loading}>
              {loading ? <span className="material-symbols-outlined animate-spin">progress_activity</span> : 'Crear cuenta'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', fontSize: '13px', color: 'rgba(255,255,255,0.85)', marginTop: '16px' }}>
          ¿Ya tienes cuenta? <Link to="/login" style={{ color: '#bfdbfe', fontWeight: 700 }}>Inicia sesión</Link>
        </p>
      </div>
    </div>
  );
}
