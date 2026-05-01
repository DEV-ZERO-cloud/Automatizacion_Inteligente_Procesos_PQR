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
        const url = URL.createObjectURL(blob);
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
  }, [isOpen, currentFile, currentFileIndex]);

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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f9fafb', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {currentFile.nombre}
          </span>
          <span style={{ fontSize: '11px', color: '#6b7280', flexShrink: 0 }}>
            ({currentFileIndex + 1} / {files.length})
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isImage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginRight: '8px' }}>
              <button onClick={handleZoomOut} style={{ padding: '4px', borderRadius: '4px', border: 'none', background: 'transparent', cursor: 'pointer' }} title="Alejar">
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>remove</span>
              </button>
              <button onClick={handleZoomReset} style={{ padding: '2px 6px', fontSize: '11px', borderRadius: '4px', border: 'none', background: 'transparent', cursor: 'pointer' }} title="Restablecer zoom">
                {Math.round(zoom * 100)}%
              </button>
              <button onClick={handleZoomIn} style={{ padding: '4px', borderRadius: '4px', border: 'none', background: 'transparent', cursor: 'pointer' }} title="Acercar">
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>add</span>
              </button>
            </div>
          )}
          
          <button onClick={handleDownload} style={{ padding: '4px', borderRadius: '4px', border: 'none', background: 'transparent', cursor: 'pointer' }} title="Descargar">
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>download</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f3f4f6', padding: '8px', overflow: 'auto', minHeight: 0 }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6b7280' }}>
            <span className="material-symbols-outlined animate-spin">sync</span>
            Cargando...
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', color: '#ef4444', padding: '16px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '36px' }}>error</span>
            <p>Error al cargar la vista previa</p>
            <button onClick={handleDownload} className="mt-2 btn btn-primary btn-sm">Descargar archivo</button>
          </div>
        ) : isImage && previewUrl ? (
          <img
            src={previewUrl}
            alt={currentFile.nombre}
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: 'center center',
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        ) : isPdf && previewUrl ? (
          <iframe src={previewUrl} title={currentFile.nombre} style={{ width: '100%', height: '100%', border: 'none' }} />
        ) : (
          <div style={{ textAlign: 'center', color: '#6b7280', padding: '16px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '36px' }}>description</span>
            <p>Vista previa no disponible</p>
            <button onClick={handleDownload} className="mt-2 btn btn-primary btn-sm">Descargar archivo</button>
          </div>
        )}
      </div>

      {/* Navigation */}
      {files.length > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderTop: '1px solid #e5e7eb', backgroundColor: '#f9fafb', flexShrink: 0 }}>
          <button
            onClick={handlePrev}
            disabled={currentFileIndex === 0}
            style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', fontSize: '12px', borderRadius: '4px', border: 'none', background: currentFileIndex === 0 ? 'transparent' : 'transparent', color: currentFileIndex === 0 ? '#d1d5db' : '#4b5563', cursor: currentFileIndex === 0 ? 'not-allowed' : 'pointer' }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>arrow_back</span>
            Anterior
          </button>
          
          <div style={{ display: 'flex', gap: '4px' }}>
            {files.map((_, idx) => (
              <button
                key={idx}
                onClick={() => onFileChange(idx)}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  border: 'none',
                  background: idx === currentFileIndex ? '#2563eb' : '#d1d5db',
                  cursor: 'pointer'
                }}
                title={`Archivo ${idx + 1}`}
              />
            ))}
          </div>
          
          <button
            onClick={handleNext}
            disabled={currentFileIndex === files.length - 1}
            style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', fontSize: '12px', borderRadius: '4px', border: 'none', background: 'transparent', color: currentFileIndex === files.length - 1 ? '#d1d5db' : '#4b5563', cursor: currentFileIndex === files.length - 1 ? 'not-allowed' : 'pointer' }}
          >
            Siguiente
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>arrow_forward</span>
          </button>
        </div>
      )}
    </div>
  );
}