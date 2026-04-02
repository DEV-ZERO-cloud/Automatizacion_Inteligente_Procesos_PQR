export function Ajustes() {
  return (
    <div>
      <div className="page-header animate-fade-in">
        <h1 className="page-title">Configuración</h1>
        <p className="page-subtitle">Ajustes del sistema</p>
      </div>

      <div style={{ display: 'grid', gap: '24px' }}>
        <div className="card animate-fade-in">
          <div style={{ padding: '24px', borderBottom: '1px solid #f2f4f7' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>General</h3>
          </div>
          <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Nombre de la Empresa</label>
              <input className="input" defaultValue="Sistema PQR" style={{ maxWidth: '400px' }} />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Correo de Contacto</label>
              <input className="input" type="email" defaultValue="contacto@pqr.com" style={{ maxWidth: '400px' }} />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#525f73', marginBottom: '8px' }}>Zona Horaria</label>
              <select className="select" style={{ maxWidth: '400px' }}>
                <option>America/Bogota (GMT-5)</option>
                <option>America/Lima (GMT-5)</option>
                <option>America/Mexico_City (GMT-6)</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card animate-fade-in">
          <div style={{ padding: '24px', borderBottom: '1px solid #f2f4f7' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Clasificación IA</h3>
          </div>
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <p style={{ fontWeight: '600', marginBottom: '4px' }}>Umbral de Confianza</p>
                <p style={{ fontSize: '13px', color: '#525f73' }}>Clasificaciones por debajo de este umbral requieren validación manual</p>
              </div>
              <input type="number" className="input" defaultValue="70" style={{ width: '100px', textAlign: 'center' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <p style={{ fontWeight: '600', marginBottom: '4px' }}>Auto-clasificación</p>
                <p style={{ fontSize: '13px', color: '#525f73' }}>Permitir clasificación automática de nuevas PQRs</p>
              </div>
              <button className="btn btn-sm btn-primary">Activado</button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: '600', marginBottom: '4px' }}>Reentrenamiento Automático</p>
                <p style={{ fontSize: '13px', color: '#525f73' }}>Reentrenar modelo semanalmente con nuevos datos</p>
              </div>
              <button className="btn btn-sm btn-secondary">Desactivado</button>
            </div>
          </div>
        </div>

        <div className="card animate-fade-in">
          <div style={{ padding: '24px' }}>
            <button className="btn btn-primary" style={{ marginRight: '12px' }}>Guardar Cambios</button>
            <button className="btn btn-secondary">Cancelar</button>
          </div>
        </div>
      </div>
    </div>
  );
}
