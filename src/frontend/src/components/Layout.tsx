import { Outlet } from 'react-router-dom';
import { Sidebar } from './common/Sidebar';
import { Topbar } from './common/Topbar';

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <Topbar />
      <main className="layout-main">
        <div className="layout-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
