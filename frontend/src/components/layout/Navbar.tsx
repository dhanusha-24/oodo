import React from 'react';
import { Menu, LogOut, Sparkles, Building2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavbarProps {
  onToggleSidebar: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, tenant, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors focus:outline-none"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200/80 text-xs text-slate-700 font-medium">
          <Building2 className="w-3.5 h-3.5 text-indigo-600" />
          <span>{tenant?.name || 'Acme Cloud Technologies'}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Hackathon Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Hackathon MVP Live</span>
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold text-slate-800">{user?.full_name || 'Admin User'}</p>
            <p className="text-[11px] text-slate-500">{user?.email || 'owner@acme.com'}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-indigo-600 text-white font-semibold text-sm flex items-center justify-center shadow-sm">
            {user?.full_name?.charAt(0) || 'A'}
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
