import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { BandejaEntrada } from './pages/BandejaEntrada';
import { RegistroPQR } from './pages/RegistroPQR';
import { Reportes } from './pages/Reportes';
import { GestionUsuarios } from './pages/GestionUsuarios';
import { GestionIA } from './pages/GestionIA';
import { Ajustes } from './pages/Ajustes';
import { useAuthStore } from './stores/authStore';
import { pqrService } from './services/pqrService';
import type { PQR } from './types';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function DetallePQR() {
  const { id } = useParams();
  const [pqr, setPqr] = useState<PQR | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const loadPqr = async () => {
      if (!id) {
        setError('Identificador de PQR invalido.');
        setLoading(false);
        return;
      }

      try {
        const data = await pqrService.getById(Number(id));
        if (isMounted) {
          setPqr(data);
          setError('');
        }
      } catch {
        if (isMounted) {
          setError('No fue posible cargar la PQR solicitada.');
          setPqr(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadPqr();
    return () => {
      isMounted = false;
    };
  }, [id]);

  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Detalle de PQR</h1>
        <p className="page-subtitle">Información detallada de la solicitud</p>
      </div>
      <div className="card" style={{ padding: '32px' }}>
        {loading ? (
          <p style={{ color: '#525f73' }}>Cargando...</p>
        ) : error ? (
          <p style={{ color: '#b91c1c' }}>{error}</p>
        ) : pqr ? (
          <div style={{ display: 'grid', gap: '16px' }}>
            <div>
              <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>ID</p>
              <p style={{ fontWeight: '700', fontFamily: 'monospace' }}>#{pqr.id}</p>
            </div>
            <div>
              <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Titulo</p>
              <p style={{ fontWeight: '700' }}>{pqr.titulo}</p>
            </div>
            <div>
              <p style={{ fontSize: '12px', color: '#525f73', marginBottom: '4px' }}>Descripcion</p>
              <p>{pqr.descripcion}</p>
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{pqr.tipo}</span>
              <span className="badge badge-primary">{pqr.categoria || 'Sin categoria'}</span>
              <span className="badge badge-warning">{pqr.prioridad || 'Sin prioridad'}</span>
              <span className="badge badge-success">{pqr.estado}</span>
            </div>
          </div>
        ) : (
          <p style={{ color: '#525f73' }}>No hay informacion disponible.</p>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="bandeja-entrada" element={<BandejaEntrada />} />
          <Route path="registro-pqr" element={<RegistroPQR />} />
          <Route path="reportes" element={<Reportes />} />
          <Route path="usuarios" element={<GestionUsuarios />} />
          <Route path="gestion-ia" element={<GestionIA />} />
          <Route path="ajustes" element={<Ajustes />} />
          <Route path="pqr/:id" element={<DetallePQR />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
