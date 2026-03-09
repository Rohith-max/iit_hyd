import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileInput, Activity, Bell } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/intake', label: 'New Analysis', icon: FileInput },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-nexus-dark-bg text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b border-nexus-dark-border bg-nexus-dark-bg/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-nexus-cyan/20 to-nexus-cyan/5 border border-nexus-cyan/30">
              <span className="text-nexus-cyan font-bold text-sm font-mono">N</span>
            </div>
            <span className="text-lg font-semibold tracking-tight">
              <span className="text-white">NEXUS</span>
              <span className="text-nexus-cyan ml-1">CREDIT</span>
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition-all',
                  location.pathname === to
                    ? 'bg-white/10 text-white'
                    : 'text-white/50 hover:text-white hover:bg-white/5',
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-4">
            <button className="relative text-white/50 hover:text-white transition-colors">
              <Bell size={18} />
              <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-nexus-cyan" />
            </button>
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-nexus-cyan/30 to-nexus-cyan/10 border border-nexus-cyan/20 flex items-center justify-center">
              <span className="text-xs font-semibold text-nexus-cyan">A</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
