'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { User } from '@/lib/types';
import { authService } from '@/lib/api';
import {
  Home,
  FileText,
  Plus,
  User as UserIcon,
  LogOut,
  ChevronLeft,
  Users,
  BarChart3,
  ClipboardList
} from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/login');
        return;
      }
      try {
        const userData = await authService.getMe();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (error) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  const getMenuItems = () => {
    switch (user?.rol) {
      case 'usuario':
        return [
          { href: '/dashboard', icon: Home, label: 'Inicio' },
          { href: '/dashboard/mis-pqrs', icon: ClipboardList, label: 'Mis PQR\'s' },
          { href: '/dashboard/nueva-pqr', icon: Plus, label: 'Nueva PQR' },
        ];
      case 'supervisor':
        return [
          { href: '/dashboard', icon: Home, label: 'Inicio' },
          { href: '/dashboard/pqrs-asignadas', icon: FileText, label: 'PQR\'s Asignadas' },
        ];
      case 'operador':
        return [
          { href: '/dashboard', icon: Home, label: 'Dashboard' },
          { href: '/dashboard/todas-pqrs', icon: ClipboardList, label: 'Todas las PQR\'s' },
          { href: '/dashboard/usuarios', icon: Users, label: 'Usuarios' },
          { href: '/dashboard/estadisticas', icon: BarChart3, label: 'Estadísticas' },
        ];
      default:
        return [];
    }
  };

  const getRoleLabel = () => {
    switch (user?.rol) {
      case 'usuario': return 'Usuario';
      case 'supervisor': return 'Supervisor';
      case 'operador': return 'Operador';
      default: return '';
    }
  };

  return (
    <div className="min-h-screen bg-secondary flex">
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-white shadow-lg transition-all duration-300 flex flex-col`}
      >
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            {sidebarOpen && (
              <div>
                <h1 className="font-bold text-gray-800 text-lg">ProjectProbe</h1>
                <p className="text-xs text-gray-500">PQR System</p>
              </div>
            )}
          </div>
        </div>

        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-3 top-20 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center hover:bg-gray-50"
        >
          <ChevronLeft
            className={`w-4 h-4 text-gray-500 transition-transform ${!sidebarOpen && 'rotate-180'}`}
          />
        </button>

        <nav className="flex-1 p-4 space-y-2">
          {getMenuItems().map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="sidebar-link"
            >
              <item.icon className="w-5 h-5" />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className={`flex items-center gap-3 ${!sidebarOpen && 'justify-center'}`}>
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-primary-600" />
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-800 text-sm truncate">{user?.nombre}</p>
                <p className="text-xs text-gray-500">{getRoleLabel()}</p>
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className={`mt-3 w-full sidebar-link text-red-500 hover:bg-red-50 ${!sidebarOpen && 'justify-center'}`}
          >
            <LogOut className="w-5 h-5" />
            {sidebarOpen && <span>Cerrar Sesión</span>}
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
