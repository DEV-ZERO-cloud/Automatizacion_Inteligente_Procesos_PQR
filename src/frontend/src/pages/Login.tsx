import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuthStore } from '../stores/authStore';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError('Complete todos los campos'); return; }
    setLoading(true);
    setError('');
    try {
      const response = await authService.login(email, password);
      login(response.user, response.access_token);
      navigate('/');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || 'Credenciales inválidas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(160deg, #0b3b7a 0%, #1f2937 60%, #0f766e 100%)', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '420px' }}>
        <div className="card animate-fade-in" style={{ padding: '40px' }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div className="stat-icon" style={{ width: '64px', height: '64px', margin: '0 auto 16px' }}>
              <span className="material-symbols-outlined text-white" style={{ fontSize: '32px' }}>account_balance</span>
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px' }}>Gestión PQR</h1>
            <p style={{ color: '#525f73', fontSize: '14px' }}>Inicie sesión en su cuenta</p>
          </div>

          {error && (
            <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '12px 16px', borderRadius: '10px', marginBottom: '20px', fontSize: '14px', fontWeight: '500' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                Correo electrónico
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="correo@ejemplo.com"
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#525f73', marginBottom: '8px' }}>
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? (
                <span className="material-symbols-outlined animate-spin">progress_activity</span>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', fontSize: '12px', color: 'rgba(255,255,255,0.7)', marginTop: '24px' }}>
          Sistema de Automatización Inteligente de Procesos PQR
        </p>
        <p style={{ textAlign: 'center', fontSize: '13px', color: 'rgba(255,255,255,0.9)', marginTop: '10px' }}>
          ¿No tienes cuenta? <Link to="/register" style={{ color: '#bfdbfe', fontWeight: 700 }}>Regístrate</Link>
        </p>
      </div>
    </div>
  );
}
