import { useEffect, useState, useRef, useMemo } from 'react';
import { pqrService } from '../services/pqrService';
import { reportService } from '../services/reportService';
import { iaService } from '../services/iaService';
import type { DebugStatus, TrainingCsv, TrainResult } from '../services/iaService';
import type { Classification } from '../types';

function fmtBytes(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1048576).toFixed(1)} MB`;
}
function confPct(v: number) { return v <= 1 ? Math.round(v * 100) : Math.round(v); }

export function GestionIA() {
  const [status, setStatus] = useState<DebugStatus | null>(null);
  const [csvFiles, setCsvFiles] = useState<TrainingCsv[]>([]);
  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [totalPqrs, setTotalPqrs] = useState(0);
  const [error, setError] = useState('');

  // Training state
  const [selectedCsv, setSelectedCsv] = useState('');
  const [trainTarget, setTrainTarget] = useState('all');
  const [minPerClass, setMinPerClass] = useState(5);
  const [training, setTraining] = useState(false);
  const [trainProgress, setTrainProgress] = useState(0);
  const [trainResult, setTrainResult] = useState<TrainResult | null>(null);
  const [trainError, setTrainError] = useState('');

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  // Action states
  const [reloading, setReloading] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const refresh = async () => {
    setError('');
    try {
      const [s, files, cls, dash] = await Promise.all([
        iaService.getDebugStatus(), iaService.listCsvFiles(),
        pqrService.getAllClassifications(), reportService.getDashboard(),
      ]);
      setStatus(s); setCsvFiles(files); setClassifications(cls); setTotalPqrs(dash.total);
    } catch { setError('No se pudo conectar con el servicio de IA.'); }
  };

  useEffect(() => { refresh(); }, []);

  const avgConf = useMemo(() => {
    if (!classifications.length) return 0;
    return Math.round(classifications.reduce((a, c) => a + confPct(c.confianza), 0) / classifications.length);
  }, [classifications]);

  const coverage = useMemo(() => totalPqrs ? Math.round((classifications.length / totalPqrs) * 100) : 0, [classifications, totalPqrs]);

  const handleUpload = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) return;
    setUploading(true); setUploadMsg('');
    try {
      const r = await iaService.uploadCsv(f);
      setUploadMsg(r.valid ? `✓ ${r.filename} subido (${r.rows} filas)` : `⚠ ${r.filename}: faltan columnas ${r.missing_columns.join(', ')}`);
      await refresh();
    } catch { setUploadMsg('Error al subir el archivo.'); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleTrain = async () => {
    if (!selectedCsv) return;
    setTraining(true); setTrainResult(null); setTrainError(''); setTrainProgress(0);
    const interval = setInterval(() => setTrainProgress(p => Math.min(p + Math.random() * 8, 92)), 800);
    try {
      const csv = csvFiles.find(f => f.filename === selectedCsv);
      const r = await iaService.train(csv?.path || selectedCsv, trainTarget, minPerClass);
      setTrainResult(r); setTrainProgress(100);
      await refresh();
    } catch (e: any) {
      setTrainError(e?.response?.data?.detail || 'Error durante el entrenamiento.');
    }
    clearInterval(interval); setTraining(false);
  };

  const handleReload = async (type: 'rules' | 'models') => {
    setReloading(type); setActionMsg('');
    try {
      if (type === 'rules') {
        const r = await iaService.reloadRules();
        setActionMsg(`✓ ${r.rules_count} reglas recargadas`);
      } else {
        const r = await iaService.reloadModels();
        setActionMsg(`✓ Modelos: cat=${r.models_ready.category ? '✓' : '✗'} pri=${r.models_ready.priority ? '✓' : '✗'}`);
      }
      await refresh();
    } catch { setActionMsg('Error al recargar.'); }
    setReloading('');
  };

  // Styles
  const S = {
    page: { minHeight: '100vh', paddingBottom: 40 } as React.CSSProperties,
    topBar: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap' as const, gap: 12 },
    title: { fontSize: 22, fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10 },
    titleIcon: { fontSize: 28, color: '#7c3aed' },
    card: { background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', marginBottom: 16, overflow: 'hidden' as const },
    cardHead: { padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
    cardTitle: { fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 },
    cardBody: { padding: 20 },
    grid3: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 },
    grid2: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 },
    metric: { textAlign: 'center' as const, padding: 20, background: '#f8fafc', borderRadius: 12, border: '1px solid #f1f5f9' },
    metricVal: (color: string) => ({ fontSize: 32, fontWeight: 800, color, lineHeight: 1.2 }),
    metricLabel: { fontSize: 12, color: '#64748b', marginTop: 6 },
    statusDot: (ok: boolean) => ({ width: 10, height: 10, borderRadius: '50%', background: ok ? '#22c55e' : '#ef4444', display: 'inline-block', marginRight: 8 }),
    btn: (color: string, disabled = false) => ({ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: 'none', fontWeight: 600, fontSize: 13, cursor: disabled ? 'not-allowed' : 'pointer', background: color, color: '#fff', opacity: disabled ? 0.5 : 1, transition: 'all .2s' }) as React.CSSProperties,
    progress: { width: '100%', height: 8, background: '#e2e8f0', borderRadius: 8, overflow: 'hidden' as const, marginTop: 12 },
    progressFill: (pct: number) => ({ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, #7c3aed, #2563eb)', borderRadius: 8, transition: 'width 0.4s ease' }),
    fileRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #f1f5f9', transition: 'background .15s', cursor: 'pointer' } as React.CSSProperties,
    mono: { fontFamily: 'monospace', fontSize: 12, color: '#7c3aed', fontWeight: 600 },
    select: { padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13, fontWeight: 500, minWidth: 180, background: '#fff' },
    input: { padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13, width: 80 },
    alert: (type: 'ok' | 'err' | 'warn') => ({ padding: '10px 16px', borderRadius: 10, fontSize: 13, fontWeight: 500, marginBottom: 12, background: type === 'ok' ? '#f0fdf4' : type === 'err' ? '#fef2f2' : '#fffbeb', color: type === 'ok' ? '#166534' : type === 'err' ? '#991b1b' : '#92400e', border: `1px solid ${type === 'ok' ? '#bbf7d0' : type === 'err' ? '#fecaca' : '#fde68a'}` }),
    sectionTitle: { fontSize: 18, fontWeight: 800, color: '#1e293b', marginBottom: 16, marginTop: 32, display: 'flex', alignItems: 'center', gap: 8 } as React.CSSProperties,
  };

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={S.topBar}>
        <div>
          <h1 style={S.title}>
            <span className="material-symbols-outlined" style={S.titleIcon}>precision_manufacturing</span>
            Centro de Control IA
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>Entrenamiento, modelos y configuración del agente inteligente</p>
        </div>
      </div>

      {error && <div style={S.alert('err')}>{error}</div>}
      {actionMsg && <div style={S.alert(actionMsg.startsWith('✓') ? 'ok' : 'err')}>{actionMsg}</div>}

      {/* ═══ ESTADO TAB ═══ */}
      <div style={{ marginBottom: 40 }}>
        {/* KPI Cards */}
        <div style={S.grid3}>
          <div style={S.metric}>
            <div style={S.metricVal('#7c3aed')}>{avgConf}%</div>
            <div style={S.metricLabel}>Confianza Promedio</div>
          </div>
          <div style={S.metric}>
            <div style={S.metricVal('#2563eb')}>{coverage}%</div>
            <div style={S.metricLabel}>Cobertura ({classifications.length}/{totalPqrs})</div>
          </div>
          <div style={S.metric}>
            <div style={S.metricVal('#059669')}>{status?.rules_count ?? '—'}</div>
            <div style={S.metricLabel}>Reglas Activas</div>
          </div>
        </div>

        <div style={{ ...S.grid2, marginTop: 16 }}>
          {/* System Status */}
          <div style={S.card}>
            <div style={S.cardHead}>
              <span style={S.cardTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#7c3aed' }}>dns</span>
                Estado del Sistema
              </span>
              <button style={S.btn('#7c3aed')} onClick={refresh}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>refresh</span> Actualizar
              </button>
            </div>
            <div style={S.cardBody}>
              {status ? (
                <div style={{ display: 'grid', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Embedding Model</span>
                    <span style={S.mono}>{status.embedding_model}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Embeddings</span>
                    <span><span style={S.statusDot(status.embedding_ready)} />{status.embedding_ready ? 'Listo' : 'No cargado'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Clasificador Categoría</span>
                    <span><span style={S.statusDot(status.classifiers.category.ready)} />{status.classifiers.category.ready ? `${status.classifiers.category.classes.length} clases` : 'Sin entrenar'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Clasificador Prioridad</span>
                    <span><span style={S.statusDot(status.classifiers.priority.ready)} />{status.classifiers.priority.ready ? `${status.classifiers.priority.classes.length} clases` : 'Sin entrenar'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Modo Activo</span>
                    <span className="badge badge-primary" style={{ fontSize: 11 }}>{status.active_mode}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Umbral Confianza</span>
                    <span style={{ fontWeight: 700 }}>{(status.confidence_threshold * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ) : <p style={{ color: '#94a3b8', fontSize: 13 }}>Cargando estado...</p>}
            </div>
          </div>

          {/* Actions */}
          <div style={S.card}>
            <div style={S.cardHead}>
              <span style={S.cardTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#2563eb' }}>build</span>
                Acciones del Sistema
              </span>
            </div>
            <div style={S.cardBody}>
              <div style={{ display: 'grid', gap: 12 }}>
                <div style={{ padding: 16, background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>Recargar Reglas</h4>
                  <p style={{ fontSize: 12, color: '#64748b', marginBottom: 12 }}>Recarga rules.yaml en caliente sin reiniciar el servicio.</p>
                  <button style={S.btn('#2563eb', reloading === 'rules')} onClick={() => handleReload('rules')} disabled={!!reloading}>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{reloading === 'rules' ? 'sync' : 'rule'}</span>
                    {reloading === 'rules' ? 'Recargando...' : 'Recargar Reglas'}
                  </button>
                </div>
                <div style={{ padding: 16, background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>Recargar Modelos ML</h4>
                  <p style={{ fontSize: 12, color: '#64748b', marginBottom: 12 }}>Recarga los clasificadores desde disco después de un entrenamiento.</p>
                  <button style={S.btn('#059669', reloading === 'models')} onClick={() => handleReload('models')} disabled={!!reloading}>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{reloading === 'models' ? 'sync' : 'model_training'}</span>
                    {reloading === 'models' ? 'Recargando...' : 'Recargar Modelos'}
                  </button>
                </div>
                {status?.classifiers.category.ready && (
                  <div style={{ padding: 16, background: '#faf5ff', borderRadius: 12, border: '1px solid #e9d5ff' }}>
                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Clases Detectadas</h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {status.classifiers.category.classes.map(c => (
                        <span key={c} style={{ padding: '4px 10px', borderRadius: 6, background: '#ede9fe', color: '#6d28d9', fontSize: 11, fontWeight: 600 }}>{c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <h2 style={S.sectionTitle}>
        <span className="material-symbols-outlined" style={{ color: '#7c3aed' }}>folder_open</span>
        Gestión de Datasets
      </h2>

      {/* ═══ DATASETS TAB ═══ */}
      <div style={{ marginBottom: 40 }}>
        <div style={S.card}>
          <div style={S.cardHead}>
            <span style={S.cardTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#2563eb' }}>upload_file</span>
              Subir Dataset
            </span>
          </div>
          <div style={{ ...S.cardBody, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <input ref={fileRef} type="file" accept=".csv" style={{ fontSize: 13 }} />
            <button style={S.btn('#2563eb', uploading)} onClick={handleUpload} disabled={uploading}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{uploading ? 'sync' : 'cloud_upload'}</span>
              {uploading ? 'Subiendo...' : 'Subir CSV'}
            </button>
            {uploadMsg && <span style={{ fontSize: 13, color: uploadMsg.startsWith('✓') ? '#059669' : '#d97706' }}>{uploadMsg}</span>}
            <p style={{ fontSize: 11, color: '#94a3b8', width: '100%' }}>El CSV debe contener las columnas: <code>texto</code>, <code>categoria</code>, <code>prioridad</code></p>
          </div>
        </div>

        <div style={S.card}>
          <div style={S.cardHead}>
            <span style={S.cardTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#7c3aed' }}>folder_open</span>
              Datasets Disponibles ({csvFiles.length})
            </span>
          </div>
          <div>
            {csvFiles.length > 0 ? csvFiles.map(f => (
              <div key={f.filename} style={S.fileRow} onClick={() => { setSelectedCsv(f.filename); document.getElementById('train-section')?.scrollIntoView({ behavior: 'smooth' }); }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#7c3aed' }}>description</span>
                  <div>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{f.filename}</span>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{f.rows} filas · {fmtBytes(f.size_bytes)} · {new Date(f.modified * 1000).toLocaleDateString('es-CO')}</div>
                  </div>
                </div>
                <button style={S.btn('#7c3aed')} onClick={e => { e.stopPropagation(); setSelectedCsv(f.filename); document.getElementById('train-section')?.scrollIntoView({ behavior: 'smooth' }); }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>play_arrow</span> Entrenar
                </button>
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 48, marginBottom: 12, display: 'block' }}>folder_off</span>
                <p>No hay datasets disponibles. Sube un CSV para comenzar.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <h2 id="train-section" style={S.sectionTitle}>
        <span className="material-symbols-outlined" style={{ color: '#059669' }}>model_training</span>
        Entrenamiento de Modelos
      </h2>

      {/* ═══ TRAIN TAB ═══ */}
      <div style={S.grid2}>
        <div style={S.card}>
          <div style={S.cardHead}>
            <span style={S.cardTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#7c3aed' }}>settings</span>
              Configurar Entrenamiento
            </span>
          </div>
          <div style={S.cardBody}>
            <div style={{ display: 'grid', gap: 16 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6, display: 'block' }}>Dataset CSV</label>
                <select style={S.select} value={selectedCsv} onChange={e => setSelectedCsv(e.target.value)}>
                  <option value="">— Seleccionar CSV —</option>
                  {csvFiles.map(f => <option key={f.filename} value={f.filename}>{f.filename} ({f.rows} filas, {fmtBytes(f.size_bytes)})</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6, display: 'block' }}>Objetivo</label>
                <select style={S.select} value={trainTarget} onChange={e => setTrainTarget(e.target.value)}>
                  <option value="all">Ambos (Categoría + Prioridad)</option>
                  <option value="categoria">Solo Categoría</option>
                  <option value="prioridad">Solo Prioridad</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6, display: 'block' }}>Mín. ejemplos/clase</label>
                <input type="number" style={S.input} value={minPerClass} onChange={e => setMinPerClass(Number(e.target.value))} min={2} />
              </div>
              <button style={S.btn('#7c3aed', training || !selectedCsv)} onClick={handleTrain} disabled={training || !selectedCsv}>
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{training ? 'sync' : 'rocket_launch'}</span>
                {training ? 'Entrenando...' : 'Iniciar Entrenamiento'}
              </button>
              {training && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                    <span>Progreso estimado</span><span>{Math.round(trainProgress)}%</span>
                  </div>
                  <div style={S.progress}><div style={S.progressFill(trainProgress)} /></div>
                  <p style={{ fontSize: 11, color: '#94a3b8', marginTop: 8 }}>Generando embeddings y entrenando clasificadores. Puede tomar entre 30s y 5min dependiendo del dataset.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={S.card}>
          <div style={S.cardHead}>
            <span style={S.cardTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#059669' }}>analytics</span>
              Resultados
            </span>
          </div>
          <div style={S.cardBody}>
            {trainError && <div style={S.alert('err')}>{trainError}</div>}
            {trainResult ? (
              <div style={{ display: 'grid', gap: 14 }}>
                <div style={S.alert('ok')}>Entrenamiento completado — {trainResult.samples} muestras procesadas</div>
                {Object.entries(trainResult.models).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                    <span style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{k}</span>
                    <span style={{ fontWeight: 600, fontSize: 13, color: v.startsWith('ok') ? '#059669' : '#d97706' }}>{v}</span>
                  </div>
                ))}
                <p style={{ fontSize: 12, color: '#64748b' }}>Los modelos se recargaron automáticamente. El sistema ya está usando los nuevos clasificadores.</p>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 48, marginBottom: 12, display: 'block' }}>science</span>
                <p style={{ fontSize: 14, fontWeight: 500 }}>Selecciona un dataset y ejecuta el entrenamiento para ver resultados aquí.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
