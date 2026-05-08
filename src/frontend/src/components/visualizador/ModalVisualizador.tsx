import { useState, useEffect } from 'react';
import type { PQRFile } from '../../types';
import { fileService } from '../../services/fileService';

interface ModalVisualizadorProps {
  isOpen: boolean;
  onClose: () => void;
  files: PQRFile[];
  currentFileIndex: number;
  onFileChange: (index: number) => void;
}

export function ModalVisualizador({ isOpen, onClose, files, currentFileIndex, onFileChange }: ModalVisualizadorProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState(false);

  const currentFile = files[currentFileIndex];

  useEffect(() => {
    if (!isOpen || !currentFile) return;

    const loadPreview = async () => {
      setLoading(true);
      setError(false);
      setZoom(1);
      try {
        const blob = await fileService.getFileBlob(currentFile.id);
        // CRÍTICO: Asegurar que el blob tenga el tipo MIME correcto para que el navegador sepa cómo renderizarlo
        const typedBlob = new Blob([blob], { type: currentFile.tipo || 'application/octet-stream' });
        const url = URL.createObjectURL(typedBlob);
        setPreviewUrl(url);
      } catch {
        setError(true);
        setPreviewUrl(null);
      } finally {
        setLoading(false);
      }
    };

    loadPreview();

    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [isOpen, currentFile]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && currentFileIndex > 0) {
        onFileChange(currentFileIndex - 1);
      }
      if (e.key === 'ArrowRight' && currentFileIndex < files.length - 1) {
        onFileChange(currentFileIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, currentFileIndex, files.length, onFileChange]);

  if (!isOpen || !currentFile) return null;

  const isImage = currentFile.tipo?.startsWith('image/');
  const isPdf = currentFile.tipo === 'application/pdf';

  const handleZoomIn = () => setZoom(z => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom(z => Math.max(z - 0.25, 0.5));
  const handleZoomReset = () => setZoom(1);

  const handlePrev = () => {
    if (currentFileIndex > 0) onFileChange(currentFileIndex - 1);
  };

  const handleNext = () => {
    if (currentFileIndex < files.length - 1) onFileChange(currentFileIndex + 1);
  };

  const handleDownload = async () => {
    if (!currentFile) return;
    try {
      const blob = await fileService.getFileBlob(currentFile.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = currentFile.nombre;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', backgroundColor: '#ffffff', color: '#1e293b' }}>
      {/* Toolbar Superior */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '8px', backgroundColor: isImage ? '#e0f2fe' : isPdf ? '#fee2e2' : '#e0e7ff', color: isImage ? '#0ea5e9' : isPdf ? '#ef4444' : '#6366f1' }}>
             <span className="material-symbols-outlined">{isImage ? 'image' : isPdf ? 'picture_as_pdf' : 'insert_drive_file'}</span>
          </div>
          <div style={{ minWidth: 0 }}>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#334155', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {currentFile.nombre}
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              Archivo {currentFileIndex + 1} de {files.length} • {currentFile.tipo || 'Desconocido'}
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {isImage && (
            <div style={{ display: 'flex', alignItems: 'center', background: '#f1f5f9', borderRadius: '8px', padding: '2px', border: '1px solid #e2e8f0' }}>
              <button onClick={handleZoomOut} style={{ padding: '6px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#475569', cursor: 'pointer', display: 'flex', alignItems: 'center' }} title="Alejar">
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>remove</span>
              </button>
              <span style={{ padding: '0 10px', fontSize: '13px', fontWeight: 600, color: '#334155', minWidth: '4ch', textAlign: 'center' }}>
                {Math.round(zoom * 100)}%
              </span>
              <button onClick={handleZoomIn} style={{ padding: '6px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#475569', cursor: 'pointer', display: 'flex', alignItems: 'center' }} title="Acercar">
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add</span>
              </button>
              <div style={{ width: '1px', height: '20px', background: '#cbd5e1', margin: '0 4px' }}></div>
              <button onClick={handleZoomReset} style={{ padding: '6px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#475569', cursor: 'pointer', display: 'flex', alignItems: 'center' }} title="Ajustar a pantalla">
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>fit_screen</span>
              </button>
            </div>
          )}
          
          <button onClick={handleDownload} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '8px', border: 'none', background: '#0f172a', color: '#fff', fontWeight: 600, fontSize: '13px', cursor: 'pointer', transition: 'background 0.2s' }} title="Descargar">
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>download</span>
            Descargar
          </button>
        </div>
      </div>

      {/* Área de Visualización */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', backgroundColor: '#f1f5f9', backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: '#64748b' }}>
            <span className="material-symbols-outlined animate-spin" style={{ fontSize: '40px', color: '#0ea5e9' }}>sync</span>
            <p style={{ margin: 0, fontSize: '14px', fontWeight: 500 }}>Preparando vista previa...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', color: '#ef4444', padding: '24px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', maxWidth: '400px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '48px', marginBottom: '12px' }}>broken_image</span>
            <h3 style={{ margin: '0 0 8px', fontSize: '16px', color: '#1e293b' }}>No se pudo cargar la vista previa</h3>
            <p style={{ margin: '0 0 20px', fontSize: '14px', color: '#64748b' }}>El archivo puede estar corrupto o el formato no es compatible con el navegador.</p>
            <button onClick={handleDownload} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: '#0f172a', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>Descargar para ver</button>
          </div>
        ) : isImage && previewUrl ? (
          <div style={{ width: '100%', height: '100%', overflow: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <img
              src={previewUrl}
              alt={currentFile.nombre}
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'center center',
                transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                borderRadius: '8px',
                backgroundColor: '#ffffff'
              }}
            />
          </div>
        ) : isPdf && previewUrl ? (
          <iframe 
            src={previewUrl} 
            title={currentFile.nombre} 
            style={{ width: '100%', height: '100%', border: 'none', backgroundColor: '#fff' }} 
          />
        ) : (
          <div style={{ textAlign: 'center', color: '#64748b', padding: '32px', background: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '64px', marginBottom: '16px', color: '#94a3b8' }}>file_present</span>
            <h3 style={{ margin: '0 0 8px', fontSize: '18px', color: '#1e293b' }}>Vista previa no disponible</h3>
            <p style={{ margin: '0 0 24px', fontSize: '14px', maxWidth: '300px' }}>Para ver el contenido de este tipo de archivo ({currentFile.tipo || 'desconocido'}), necesitas descargarlo.</p>
            <button onClick={handleDownload} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', background: '#0f172a', color: '#fff', fontWeight: 600, fontSize: '14px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>download</span>
              Descargar Archivo
            </button>
          </div>
        )}
      </div>

      {/* Navegación Inferior */}
      {files.length > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderTop: '1px solid #e2e8f0', backgroundColor: '#f8fafc', flexShrink: 0 }}>
          <button
            onClick={handlePrev}
            disabled={currentFileIndex === 0}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '13px', fontWeight: 600, borderRadius: '8px', border: '1px solid #cbd5e1', background: '#ffffff', color: currentFileIndex === 0 ? '#94a3b8' : '#334155', cursor: currentFileIndex === 0 ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>navigate_before</span>
            Anterior
          </button>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            {files.map((_, idx) => (
              <button
                key={idx}
                onClick={() => onFileChange(idx)}
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  border: 'none',
                  background: idx === currentFileIndex ? '#0ea5e9' : '#cbd5e1',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  transform: idx === currentFileIndex ? 'scale(1.2)' : 'scale(1)'
                }}
                title={`Ver archivo ${idx + 1}`}
              />
            ))}
          </div>
          
          <button
            onClick={handleNext}
            disabled={currentFileIndex === files.length - 1}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '13px', fontWeight: 600, borderRadius: '8px', border: '1px solid #cbd5e1', background: '#ffffff', color: currentFileIndex === files.length - 1 ? '#94a3b8' : '#334155', cursor: currentFileIndex === files.length - 1 ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}
          >
            Siguiente
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>navigate_next</span>
          </button>
        </div>
      )}
    </div>
  );
}