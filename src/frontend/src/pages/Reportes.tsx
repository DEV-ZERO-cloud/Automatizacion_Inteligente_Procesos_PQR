import { useEffect, useMemo, useState } from 'react';
import { reportService } from '../services/reportService';
import { pqrService } from '../services/pqrService';
import { catalogService } from '../services/catalogService';
import { useAuthStore } from '../stores/authStore';
import type { PQR } from '../types';

/* ── Paleta de series ── */
const SERIES_COLORS: Record<string, string> = {
  peticion: '#1e64c8',
  queja:    '#be123c',
  reclamo:  '#0f766e',
  total:    '#7c3aed',
};
const CAT_COLORS = ['#1e64c8','#0f766e','#c87a1e','#475569','#be123c','#7c3aed','#0891b2','#d97706'];
const PRI_COLORS = ['#be123c','#c87a1e','#475569','#64748b'];

type Bucket = { label: string; start: Date; end: Date };

function buildTimeBuckets(range: string): Bucket[] {
  const buckets: Bucket[] = [];
  const now = new Date();
  if (range === '7d') {
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6, 0, 0, 0, 0);
    for (let i = 0; i < 7; i++) {
      const d = new Date(start); d.setDate(start.getDate() + i);
      const nextD = new Date(d); nextD.setDate(d.getDate() + 1);
      buckets.push({ label: d.toLocaleDateString('es-CO', { weekday: 'short', day: '2-digit' }), start: d, end: nextD });
    }
  } else if (range === '30d') {
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 27, 0, 0, 0, 0);
    for (let i = 0; i < 4; i++) {
      const d = new Date(start); d.setDate(start.getDate() + i * 7);
      const nextD = new Date(d); nextD.setDate(d.getDate() + 7);
      buckets.push({ label: `Sem ${i+1}`, start: d, end: nextD });
    }
  } else if (range === '90d') {
    const startMonth = new Date(now.getFullYear(), now.getMonth() - 2, 1);
    for (let i = 0; i < 3; i++) {
      const d = new Date(startMonth.getFullYear(), startMonth.getMonth() + i, 1);
      const nextD = new Date(startMonth.getFullYear(), startMonth.getMonth() + i + 1, 1);
      buckets.push({ label: d.toLocaleDateString('es-CO', { month: 'long', year: 'numeric' }), start: d, end: nextD });
    }
  } else {
    const startMonth = new Date(now.getFullYear(), now.getMonth() - 11, 1);
    for (let i = 0; i < 12; i++) {
      const d = new Date(startMonth.getFullYear(), startMonth.getMonth() + i, 1);
      const nextD = new Date(startMonth.getFullYear(), startMonth.getMonth() + i + 1, 1);
      buckets.push({ label: d.toLocaleDateString('es-CO', { month: 'short' }), start: d, end: nextD });
    }
  }
  return buckets;
}

function buildSeries(pqrs: PQR[], buckets: Bucket[], tipos: string[]) {
  const map: Record<string, number[]> = {};
  tipos.forEach(t => { map[t] = new Array(buckets.length).fill(0); });
  pqrs.forEach(p => {
    const raw = p.created_at || p.updated_at;
    if (!raw) return;
    const date = new Date(raw);
    for (let i = 0; i < buckets.length; i++) {
      if (date >= buckets[i].start && date < buckets[i].end) {
        if (map[p.tipo] !== undefined) map[p.tipo][i]++;
        break;
      }
    }
  });
  return tipos.map(t => ({ tipo: t, values: map[t] }));
}

/* ── SVG Donut ── */
function DonutChart({ items, size = 160, strokeW = 28 }: { items: { name: string; cantidad: number; porcentaje: number; color: string }[]; size?: number; strokeW?: number }) {
  const cx = size / 2, cy = size / 2, r = (size - strokeW) / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  const total = items.reduce((s, i) => s + i.porcentaje, 0);
  if (total === 0) {
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e6e8eb" strokeWidth={strokeW}/>
        <text x={cx} y={cy-4} textAnchor="middle" dominantBaseline="middle" fontSize="13" fontWeight="700" fill="#94a3b8">0%</text>
        <text x={cx} y={cy+12} textAnchor="middle" dominantBaseline="middle" fontSize="10" fill="#94a3b8">Sin datos</text>
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
      {items.map((item, i) => {
        const pct = item.porcentaje / 100;
        const len = pct * circ;
        const seg = <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={item.color} strokeWidth={strokeW} strokeDasharray={`${len} ${circ - len}`} strokeLinecap="butt" strokeDashoffset={-offset} style={{ transition: 'stroke-dasharray 0.6s ease' }}/>;
        offset += len;
        return seg;
      })}
    </svg>
  );
}

/* ── Componente principal ── */
export function Reportes() {
  const { user } = useAuthStore();
  const isGerente = user?.rol_id === 'gerente';

  const [dateRange, setDateRange]         = useState('30d');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [filtroTipo, setFiltroTipo]       = useState('');
  const [filtroEstado, setFiltroEstado]   = useState('');
  const [chartType, setChartType]         = useState<'lineas' | 'barra'>('lineas');
  const [rawPqrs, setRawPqrs]             = useState<PQR[]>([]);
  const [allCategoryNames, setAllCategoryNames] = useState<string[]>([]);
  const [categories, setCategories]       = useState<{name:string;cantidad:number;porcentaje:number;color:string}[]>([]);
  const [priorities, setPriorities]       = useState<{name:string;cantidad:number;porcentaje:number;color:string}[]>([]);
  const [stats, setStats]                 = useState({ total:0, pendientes:0, enProceso:0, resueltas:0 });

  useEffect(() => {
    let ok = true;
    (async () => {
      try {
        const [dash, byCat, byPri, pqrs] = await Promise.all([
          reportService.getDashboard(), reportService.getByCategory(),
          reportService.getByPriority(), pqrService.getAll(),
        ]);
        if (!ok) return;
        const total = dash.total || 0;
        setStats({ total, pendientes: dash.pendientes, resueltas: dash.resueltas,
          enProceso: Math.max(total - dash.pendientes - dash.resueltas, 0) });
        setCategories(byCat.map((it, i) => ({
          name: it.categoria, cantidad: it.cantidad,
          porcentaje: total > 0 ? Math.round(it.cantidad/total*100) : 0,
          color: CAT_COLORS[i % CAT_COLORS.length],
        })));
        setPriorities(byPri.map((it, i) => ({
          name: it.prioridad, cantidad: it.cantidad,
          porcentaje: total > 0 ? Math.round(it.cantidad/total*100) : 0,
          color: PRI_COLORS[i % PRI_COLORS.length],
        })));
        setRawPqrs(pqrs);
      } catch { /* silent */ }
      try {
        const cats = await catalogService.getCategories();
        if (ok) setAllCategoryNames(cats.map(c => c.nombre).filter(Boolean));
      } catch { /* silent */ }
    })();
    return () => { ok = false; };
  }, []);

  const resolvedRate = stats.total ? Math.round(stats.resueltas/stats.total*100) : 0;

  const filteredForChart = useMemo(() => {
    let p = rawPqrs;
    if (filtroCategoria) p = p.filter(x => x.categoria === filtroCategoria);
    if (filtroTipo)      p = p.filter(x => x.tipo === filtroTipo);
    if (filtroEstado)    p = p.filter(x => x.estado === filtroEstado);
    return p;
  }, [rawPqrs, filtroCategoria, filtroTipo, filtroEstado]);

  const labels  = useMemo(() => buildTimeBuckets(dateRange), [dateRange]);
  const tiposPresentes = useMemo(() => {
    const base = filtroTipo ? [filtroTipo] : ['peticion','queja','reclamo'];
    return base.filter(t => filteredForChart.some(p => p.tipo === t));
  }, [filteredForChart, filtroTipo]);

  const series  = useMemo(() => buildSeries(filteredForChart, labels, tiposPresentes.length ? tiposPresentes : ['total']), [filteredForChart, labels, tiposPresentes]);
  const maxVal  = useMemo(() => Math.max(...series.flatMap(s => s.values), 1), [series]);
  const uniqueEstados = Array.from(new Set(rawPqrs.map(p => p.estado).filter(Boolean))) as string[];

  const W = 100, H = 100;
  const px = (i: number) => labels.length > 1 ? (i / (labels.length - 1)) * W : W/2;
  const py = (v: number) => H - (v / maxVal) * (H - 8) - 2;

  const gradId = 'lineGrad';

  return (
    <div>
      <div className="page-header page-header-split animate-fade-in">
        <div>
          <h1 className="page-title">{isGerente ? 'Panel Ejecutivo' : 'Reportes Estadísticos'}</h1>
          <p className="page-subtitle">{isGerente ? 'Indicadores de gestión y tendencias del sistema PQR' : 'Análisis y métricas operativas del sistema PQR'}</p>
        </div>
      </div>

      {/* KPI cards */}
      <div className="reports-stats-grid" style={{ marginBottom: '24px' }}>
        {[
          { label:'Total PQRs',      value: stats.total,      icon:'inbox',           color:'#003d9b', bg:'#dae2ff' },
          { label:'Pendientes',      value: stats.pendientes,  icon:'pending_actions', color:'#b45309', bg:'#fef3c7' },
          { label:'En Proceso',      value: stats.enProceso,   icon:'hourglass_top',  color:'#374151', bg:'#f2f4f7' },
          { label:'Resueltas',       value: stats.resueltas,   icon:'check_circle',   color:'#047857', bg:'#d1fae5' },
          { label:'Tasa Resolución', value:`${resolvedRate}%`, icon:'percent',        color:'#047857', bg:'#d1fae5' },
        ].map((s, i) => (
          <div key={s.label} className="stat-card animate-fade-in" style={{ textAlign:'center', animationDelay:`${i*0.06}s`, opacity:0 }}>
            <div style={{ width:48, height:48, borderRadius:14, background:`linear-gradient(135deg, ${s.bg}, white)`, display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 12px', boxShadow:'0 2px 8px rgba(0,0,0,0.04)' }}>
              <span className="material-symbols-outlined" style={{ color:s.color, fontSize:24 }}>{s.icon}</span>
            </div>
            <div className="stat-value" style={{ color:s.color }}>{typeof s.value === 'number' ? s.value.toLocaleString() : s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tendencias temporales */}
      <div className="card animate-fade-in" style={{ marginBottom:24, borderRadius:16, overflow:'hidden' }}>
        <div style={{ padding:'18px 24px', borderBottom:'1px solid #f2f4f7', display:'flex', flexWrap:'wrap', gap:10, alignItems:'center', justifyContent:'space-between', background:'linear-gradient(135deg, #f8fafc, #fff)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span className="material-symbols-outlined" style={{ color:'#003d9b', fontSize:20 }}>show_chart</span>
            <h2 style={{ fontSize:15, fontWeight:700 }}>Tendencias Temporales</h2>
          </div>
          <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
            <select className="select" style={{ width:140, fontSize:12, padding:'6px 10px' }} value={dateRange} onChange={e=>setDateRange(e.target.value)}>
              <option value="7d">Últimos 7 días</option>
              <option value="30d">Últimos 30 días</option>
              <option value="90d">Últimos 90 días</option>
              <option value="1y">Último año</option>
            </select>
            <select className="select" style={{ width:160, fontSize:12, padding:'6px 10px' }} value={filtroCategoria} onChange={e=>setFiltroCategoria(e.target.value)}>
              <option value="">Todas las categorías</option>
              {allCategoryNames.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select className="select" style={{ width:120, fontSize:12, padding:'6px 10px' }} value={filtroTipo} onChange={e=>setFiltroTipo(e.target.value)}>
              <option value="">Todos los tipos</option>
              <option value="peticion">Petición</option>
              <option value="queja">Queja</option>
              <option value="reclamo">Reclamo</option>
            </select>
            <select className="select" style={{ width:130, fontSize:12, padding:'6px 10px' }} value={filtroEstado} onChange={e=>setFiltroEstado(e.target.value)}>
              <option value="">Todos los estados</option>
              {uniqueEstados.map(e => <option key={e} value={e}>{e.replace('_',' ')}</option>)}
            </select>
            <div className="tabs" style={{ padding:2 }}>
              <button className={`tab ${chartType==='lineas'?'active':''}`} style={{ padding:'5px 12px', fontSize:12 }} onClick={()=>setChartType('lineas')}>
                <span className="material-symbols-outlined" style={{ fontSize:14 }}>show_chart</span> Líneas
              </button>
              <button className={`tab ${chartType==='barra'?'active':''}`} style={{ padding:'5px 12px', fontSize:12 }} onClick={()=>setChartType('barra')}>
                <span className="material-symbols-outlined" style={{ fontSize:14 }}>bar_chart</span> Barras
              </button>
            </div>
          </div>
        </div>

        <div style={{ padding:'10px 24px 0', display:'flex', gap:16, flexWrap:'wrap' }}>
          {series.map(s => (
            <div key={s.tipo} style={{ display:'flex', alignItems:'center', gap:6 }}>
              <div style={{ width:24, height:3, borderRadius:2, background: SERIES_COLORS[s.tipo] || '#003d9b' }}/>
              <span style={{ fontSize:12, color:'#525f73', textTransform:'capitalize', fontWeight:600 }}>{s.tipo}</span>
            </div>
          ))}
        </div>

        <div style={{ padding:'16px 24px 24px' }}>
          {chartType === 'lineas' ? (
            <div style={{ width:'100%', overflowX:'auto' }}>
              <div style={{ minWidth: Math.max(labels.length * 18, 300), position:'relative' }}>
                <svg viewBox="-4 -8 108 120" preserveAspectRatio="none" style={{ width:'100%', height:220, overflow:'visible', display:'block' }}>
                  <defs>
                    {series.map(s => (
                      <linearGradient key={s.tipo} id={`${gradId}_${s.tipo}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={SERIES_COLORS[s.tipo] || '#003d9b'} stopOpacity="0.35"/>
                        <stop offset="100%" stopColor={SERIES_COLORS[s.tipo] || '#003d9b'} stopOpacity="0.02"/>
                      </linearGradient>
                    ))}
                  </defs>
                  {[0,25,50,75,100].map(pct => (
                    <line key={pct} x1="0" y1={H - pct} x2={W} y2={H - pct} stroke="#e6e8eb" strokeWidth="0.5" strokeDasharray={pct===0?'none':'2,2'} />
                  ))}
                  <line x1="0" y1={H} x2={W} y2={H} stroke="#94a3b8" strokeWidth="0.8"/>
                  {series.map(s => {
                    const col = SERIES_COLORS[s.tipo] || '#003d9b';
                    const pts = s.values.map((_,i)=>`${px(i)},${py(s.values[i])}`).join(' ');
                    const fillPts = `0,${H} ${pts} ${W},${H}`;
                    return (
                      <g key={s.tipo}>
                        <polygon points={fillPts} fill={`url(#${gradId}_${s.tipo})`}/>
                        <polyline points={pts} fill="none" stroke={col} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ filter:'drop-shadow(0 1px 2px rgba(0,0,0,0.1))' }}/>
                        {s.values.map((v,i) => (
                          <circle key={i} cx={px(i)} cy={py(v)} r="2.5" fill={col} stroke="#fff" strokeWidth="1.2"/>
                        ))}
                      </g>
                    );
                  })}
                  {[[0,'min'],[Math.round(maxVal/2),'mid'],[maxVal,'max']].map(([v,k]) => (
                    <text key={k as string} x="-2" y={py(v as number)+1} textAnchor="end" fontSize="4" fill="#94a3b8">{(v as number).toLocaleString()}</text>
                  ))}
                </svg>
                <div style={{ display:'flex', justifyContent:'space-between', marginTop:4, paddingLeft:2 }}>
                  {labels.map((l,i) => (
                    <span key={i} style={{ fontSize:10, color:'#94a3b8', flex:1, textAlign:'center', whiteSpace:'nowrap' }}>{l.label}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display:'flex', gap:3, alignItems:'flex-end', height:220, overflowX:'auto', padding:'0 4px' }}>
              {labels.map((l, i) => (
                <div key={i} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', gap:2, minWidth:20 }}>
                  <div style={{ display:'flex', gap:2, alignItems:'flex-end', height:190 }}>
                    {series.map(s => {
                      const pct = maxVal > 0 ? (s.values[i]/maxVal)*100 : 0;
                      const h = Math.max(pct, s.values[i]>0 ? 4 : 0);
                      return (
                        <div
                          key={s.tipo}
                          title={`${s.tipo}: ${s.values[i]}`}
                          style={{
                            width:10,
                            background: `linear-gradient(to top, ${SERIES_COLORS[s.tipo] || '#003d9b'}, ${SERIES_COLORS[s.tipo] || '#003d9b'}88)`,
                            borderRadius:'4px 4px 0 0',
                            height:`${h}%`,
                            transition:'height 0.5s cubic-bezier(0.4,0,0.2,1)',
                            boxShadow:'0 1px 3px rgba(0,0,0,0.08)',
                          }}
                        />
                      );
                    })}
                  </div>
                  <span style={{ fontSize:9, color:'#94a3b8' }}>{l.label}</span>
                </div>
              ))}
            </div>
          )}
          <p style={{ textAlign:'center', fontSize:12, color:'#94a3b8', marginTop:8 }}>Volumen de PQRs registradas en el período seleccionado</p>
        </div>
      </div>

      {/* Distribuciones con donuts */}
      <div className="reports-charts-grid">
        <div className="card animate-fade-in" style={{ borderRadius:16, overflow:'hidden' }}>
          <div style={{ padding:'18px 24px', borderBottom:'1px solid #f2f4f7', display:'flex', alignItems:'center', gap:8, background:'linear-gradient(135deg, #f8fafc, #fff)' }}>
            <span className="material-symbols-outlined" style={{ color:'#003d9b', fontSize:20 }}>category</span>
            <h2 style={{ fontSize:15, fontWeight:700 }}>Distribución por Categoría</h2>
          </div>
          <div style={{ padding:24, display:'flex', flexDirection:'column', alignItems:'center', gap:20 }}>
            <DonutChart items={categories} size={180} strokeW={28}/>
            <div style={{ width:'100%', display:'flex', flexDirection:'column', gap:10 }}>
              {categories.length > 0 ? categories.map(cat => (
                <div key={cat.name} style={{ display:'flex', alignItems:'center', gap:10 }}>
                  <div style={{ width:10, height:10, borderRadius:'50%', background:cat.color, flexShrink:0 }}/>
                  <span style={{ flex:1, fontSize:13, color:'#374151', fontWeight:500 }}>{cat.name}</span>
                  <span style={{ fontSize:12, fontWeight:600, color:cat.color }}>{cat.cantidad}</span>
                  <span style={{ fontSize:12, color:'#94a3b8', minWidth:36, textAlign:'right' }}>{cat.porcentaje}%</span>
                </div>
              )) : <p style={{ color:'#94a3b8', fontSize:13, textAlign:'center' }}>Sin datos disponibles.</p>}
            </div>
          </div>
        </div>

        <div className="card animate-fade-in" style={{ borderRadius:16, overflow:'hidden' }}>
          <div style={{ padding:'18px 24px', borderBottom:'1px solid #f2f4f7', display:'flex', alignItems:'center', gap:8, background:'linear-gradient(135deg, #f8fafc, #fff)' }}>
            <span className="material-symbols-outlined" style={{ color:'#be123c', fontSize:20 }}>flag</span>
            <h2 style={{ fontSize:15, fontWeight:700 }}>Distribución por Prioridad</h2>
          </div>
          <div style={{ padding:24, display:'flex', flexDirection:'column', alignItems:'center', gap:20 }}>
            <DonutChart items={priorities} size={180} strokeW={28}/>
            <div style={{ width:'100%', display:'flex', flexDirection:'column', gap:10 }}>
              {priorities.length > 0 ? priorities.map(pri => (
                <div key={pri.name} style={{ display:'flex', alignItems:'center', gap:10 }}>
                  <div style={{ width:10, height:10, borderRadius:'50%', background:pri.color, flexShrink:0 }}/>
                  <span style={{ flex:1, fontSize:13, color:'#374151', fontWeight:500, textTransform:'capitalize' }}>{pri.name}</span>
                  <span style={{ fontSize:12, fontWeight:600, color:pri.color }}>{pri.cantidad}</span>
                  <span style={{ fontSize:12, color:'#94a3b8', minWidth:36, textAlign:'right' }}>{pri.porcentaje}%</span>
                </div>
              )) : <p style={{ color:'#94a3b8', fontSize:13, textAlign:'center' }}>Sin datos disponibles.</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Resumen de estado operativo */}
      <div className="card animate-fade-in" style={{ marginTop:24, padding:24, borderRadius:16 }}>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:20 }}>
          <span className="material-symbols-outlined" style={{ color:'#0f766e', fontSize:20 }}>donut_large</span>
          <h2 style={{ fontSize:15, fontWeight:700 }}>Resumen de Estado Operativo</h2>
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:16 }}>
          {[
            { label:'Tasa de Resolución', value:`${resolvedRate}%`,          color:'#047857', icon:'check_circle', bg:'#d1fae5' },
            { label:'Pendientes',         value: stats.pendientes,            color:'#b45309', icon:'hourglass_top', bg:'#fef3c7' },
            { label:'En Proceso',         value: stats.enProceso,             color:'#374151', icon:'pending_actions', bg:'#f2f4f7' },
            { label:'Categorías activas', value: categories.length,           color:'#003d9b', icon:'category', bg:'#dae2ff' },
            { label:'Prioridades',        value: priorities.length,           color:'#be123c', icon:'flag', bg:'#ffe4e6' },
          ].map(item => (
            <div key={item.label} style={{ background:`linear-gradient(135deg, ${item.bg}, white)`, borderRadius:14, padding:'16px 14px', display:'flex', alignItems:'center', gap:12, boxShadow:'0 1px 4px rgba(0,0,0,0.04)' }}>
              <div style={{ width:40, height:40, borderRadius:10, background:`${item.color}18`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                <span className="material-symbols-outlined" style={{ color:item.color, fontSize:20 }}>{item.icon}</span>
              </div>
              <div>
                <p style={{ fontSize:18, fontWeight:800, color:item.color, lineHeight:1 }}>{typeof item.value === 'number' ? item.value.toLocaleString() : item.value}</p>
                <p style={{ fontSize:11, color:'#64748b', marginTop:2 }}>{item.label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
