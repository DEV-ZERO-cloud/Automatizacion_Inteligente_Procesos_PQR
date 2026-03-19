'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authService } from '@/lib/api';
import { User } from '@/lib/types';
import {
  Plus,
  FileText,
  Clock,
  CheckCircle,
  TrendingUp,
  ArrowRight
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState({ total: 0, creadas: 0, enProceso: 0, resueltas: 0 });

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const myPqrs = await authService.getMe();
        if (user?.rol === 'usuario') {
          const pqrs = await authService.getMisPqrs();
          setStats({
            total: pqrs.length,
            creadas: pqrs.filter((p: any) => p.estado === 'creado').length,
            enProceso: pqrs.filter((p: any) => p.estado === 'en_proceso').length,
            resueltas: pqrs.filter((p: any) => p.estado === 'resuelto').length,
          });
        } else if (user?.rol === 'supervisor') {
          const pqrs = await authService.getMe();
          setStats({
            total: 0,
            creadas: 0,
            enProceso: 0,
            resueltas: 0,
          });
        }
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    };
    if (user) loadStats();
  }, [user]);

  const getRoleMessage = () => {
    switch (user?.rol) {
      case 'usuario':
        return {
          title: `¡Bienvenido, ${user?.nombre}!`,
          subtitle: 'Gestiona tus peticiones, quejas y reclamos de manera fácil y rápida.',
          action: { href: '/dashboard/nueva-pqr', label: 'Crear Nueva PQR', icon: Plus },
        };
      case 'supervisor':
        return {
          title: `Panel de Supervisor`,
          subtitle: 'Gestiona las PQR\'s asignadas a ti y mantén a los usuarios informados.',
          action: { href: '/dashboard/pqrs-asignadas', label: 'Ver PQR\'s Asignadas', icon: FileText },
        };
      case 'operador':
        return {
          title: `Panel de Operador`,
          subtitle: 'Administra todas las PQR\'s del sistema y asigna supervisores.',
          action: { href: '/dashboard/todas-pqrs', label: 'Ver Todas las PQR\'s', icon: FileText },
        };
      default:
        return { title: '', subtitle: '', action: null };
    }
  };

  const message = getRoleMessage();

  return (
    <div className="max-w-6xl mx-auto fade-in">
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white mb-8">
        <h1 className="text-3xl font-bold mb-2">{message.title}</h1>
        <p className="text-primary-100 mb-6">{message.subtitle}</p>
        {message.action && (
          <Link
            href={message.action.href}
            className="inline-flex items-center gap-2 bg-white text-primary-600 px-6 py-3 rounded-xl font-semibold hover:bg-primary-50 transition-all"
          >
            <message.action.icon className="w-5 h-5" />
            {message.action.label}
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {user?.rol === 'usuario' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={FileText}
            label="Total PQR's"
            value={stats.total}
            color="primary"
          />
          <StatCard
            icon={Clock}
            label="Creadas"
            value={stats.creadas}
            color="warning"
          />
          <StatCard
            icon={TrendingUp}
            label="En Proceso"
            value={stats.enProceso}
            color="blue"
          />
          <StatCard
            icon={CheckCircle}
            label="Resueltas"
            value={stats.resueltas}
            color="success"
          />
        </div>
      )}

      {user?.rol === 'supervisor' && (
        <div className="card">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link href="/dashboard/pqrs-asignadas" className="p-4 bg-primary-50 rounded-xl hover:bg-primary-100 transition-all">
              <FileText className="w-8 h-8 text-primary-500 mb-2" />
              <h3 className="font-semibold text-gray-800">Ver PQR's Asignadas</h3>
              <p className="text-sm text-gray-500">Gestiona las solicitudes asignadas a ti</p>
            </Link>
          </div>
        </div>
      )}

      {user?.rol === 'operador' && (
        <div className="card">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/dashboard/todas-pqrs" className="p-4 bg-primary-50 rounded-xl hover:bg-primary-100 transition-all">
              <FileText className="w-8 h-8 text-primary-500 mb-2" />
              <h3 className="font-semibold text-gray-800">Todas las PQR's</h3>
              <p className="text-sm text-gray-500">Ver y gestionar todas las solicitudes</p>
            </Link>
            <Link href="/dashboard/usuarios" className="p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-all">
              <FileText className="w-8 h-8 text-blue-500 mb-2" />
              <h3 className="font-semibold text-gray-800">Usuarios</h3>
              <p className="text-sm text-gray-500">Gestionar usuarios y supervisores</p>
            </Link>
            <Link href="/dashboard/estadisticas" className="p-4 bg-success/10 rounded-xl hover:bg-success/20 transition-all">
              <TrendingUp className="w-8 h-8 text-success mb-2" />
              <h3 className="font-semibold text-gray-800">Estadísticas</h3>
              <p className="text-sm text-gray-500">Ver métricas del sistema</p>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
  const colors = {
    primary: 'bg-primary-500',
    warning: 'bg-warning',
    blue: 'bg-blue-500',
    success: 'bg-success',
  };

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 ${colors[color as keyof typeof colors]} rounded-xl flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          <p className="text-gray text-sm">{label}</p>
        </div>
      </div>
    </div>
  );
}
