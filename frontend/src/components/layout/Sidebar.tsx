import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Layers,
  Repeat,
  FileText,
  CreditCard,
  Settings,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const { tenant } = useAuth();

  const navItems = [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Customers', to: '/customers', icon: Users },
    { label: 'Plans & Pricing', to: '/plans', icon: Layers },
    { label: 'Subscriptions', to: '/subscriptions', icon: Repeat },
    { label: 'Invoices', to: '/invoices', icon: FileText },
    { label: 'Payments', to: '/payments', icon: CreditCard },
    { label: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`bg-slate-900 text-slate-200 border-r border-slate-800 transition-all duration-300 flex flex-col fixed top-0 bottom-0 left-0 z-30 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-slate-800 gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 flex-shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              SubHub <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded uppercase font-semibold">B2B</span>
            </h1>
            <p className="text-xs text-slate-400 truncate">Subscription Engine</p>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && (
                <ChevronRight className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Tenant Context Badge */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 m-2 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Active Tenant
          </p>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-xs font-semibold text-white truncate">
              {tenant?.name || 'Acme Cloud Technologies'}
            </p>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">INR (₹) • FY 2026-27</p>
        </div>
      )}
    </aside>
  );
};
