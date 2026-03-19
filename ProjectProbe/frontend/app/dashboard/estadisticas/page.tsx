'use client';

import { useEffect, useState } from 'react';
import { pqrService } from '@/lib/api';
import { Estadisticas } from '@/lib/types';
import { BarChart3, FileText, Clock, CheckCircle, TrendingUp, PieChart } from 'lucide-react';

export default function EstadisticasPage() {
  const [stats, setStats] = useState<Estadisticas | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await pqrService.getEstadisticas();
        setStats(data);
      } catch (error) {
        console.error('Error loading stats:', error);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!stats) return null;

  const total = stats.total || 1;
  const getPercentage = (value: number) => Math.round((value / total) * 100);

  return (
    <div className="max-w-6xl mx-auto fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Estadísticas</h1>
        <p className="text-gray-500">Resumen del comportamiento del sistema</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={FileText}
          label="Total PQR's"
          value={stats.total}
          color="primary"
        />
        <StatCard
          icon={Clock}
          label="Creadas"
          value={stats.creados}
          color="warning"
          percentage={getPercentage(stats.creados)}
        />
        <StatCard
          icon={TrendingUp}
          label="En Proceso"
          value={stats.en_proceso}
          color="blue"
          percentage={getPercentage(stats.en_proceso)}
        />
        <StatCard
          icon={CheckCircle}
          label="Resueltas"
          value={stats.resueltos}
          color="success"
          percentage={getPercentage(stats.resueltos)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <PieChart className="w-6 h-6 text-primary-500" />
            Distribución por Tipo
          </h2>
          <div className="space-y-4">
            <TypeBar label="Peticiones" value={stats.por_tipo.peticion} total={total} color="primary" />
            <TypeBar label="Quejas" value={stats.por_tipo.queja} total={total} color="warning" />
            <TypeBar label="Reclamos" value={stats.por_tipo.reclamo} total={total} color="success" />
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-primary-500" />
            Estados Actuales
          </h2>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-primary-500"></div>
                <span className="text-gray-800">Creadas</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-gray-800">{stats.creados}</span>
                <span className="text-gray ml-2">({getPercentage(stats.creados)}%)</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-warning"></div>
                <span className="text-gray-800">En Proceso</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-gray-800">{stats.en_proceso}</span>
                <span className="text-gray ml-2">({getPercentage(stats.en_proceso)}%)</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-success"></div>
                <span className="text-gray-800">Resueltas</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-gray-800">{stats.resueltos}</span>
                <span className="text-gray ml-2">({getPercentage(stats.resueltos)}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, percentage }: any) {
  const colors = {
    primary: 'bg-primary-500',
    warning: 'bg-warning',
    blue: 'bg-blue-500',
    success: 'bg-success',
  };

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 ${colors[color]} rounded-xl flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          <p className="text-gray text-sm">{label}</p>
          {percentage !== undefined && (
            <p className="text-xs text-gray-500">{percentage}% del total</p>
          )}
        </div>
      </div>
    </div>
  );
}

function TypeBar({ label, value, total, color }: any) {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  const colors: Record<string, string> = {
    primary: 'bg-primary-500',
    warning: 'bg-warning',
    success: 'bg-success',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-800 font-medium">{label}</span>
        <span className="text-gray-500">{value}</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors[color]} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
}
