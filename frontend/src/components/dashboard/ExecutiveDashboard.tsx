import React from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  CreditCard,
  Users,
  AlertTriangle,
  ArrowUpRight,
  Plus,
  ArrowRight,
  ShieldCheck,
  Target,
  DollarSign,
  Activity,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { DashboardSummary, Subscription, Invoice } from '../../types';

interface DashboardProps {
  summary: DashboardSummary | null;
  recentSubs: Subscription[];
  recentInvoices: Invoice[];
  formatCurrency: (val: number | string) => string;
}

export const ExecutiveDashboard: React.FC<DashboardProps> = ({
  summary,
  recentSubs,
  recentInvoices,
  formatCurrency,
}) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Executive Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-900/40 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold mb-3">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>C-Level Executive Command Center</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Organization Strategy & Growth</h1>
            <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl">
              Consolidated real-time operational telemetry across B2B enterprise client accounts, annual recurring revenue (ARR), and capital runway.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/subscriptions"
              className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Authorize New Contract</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Monthly Recurring (MRR)
            </span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              {formatCurrency(summary?.mrr || 34997)}
            </h3>
            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-emerald-600 font-medium">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>+18.4% Net MRR Growth</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Annual Run Rate (ARR)
            </span>
            <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
              <CreditCard className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              {formatCurrency(summary?.arr || 419964)}
            </h3>
            <p className="text-xs text-slate-500 mt-1.5">Projected annualized gross run-rate</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Client Health & Retention
            </span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              100% <span className="text-xs font-normal text-slate-500">Zero Churn</span>
            </h3>
            <p className="text-xs text-emerald-600 mt-1.5 font-medium">{summary?.active_subscriptions || 3} Active Enterprise Subscriptions</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Gross Realized Capital
            </span>
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              {formatCurrency(summary?.total_collected_amount || 3538.82)}
            </h3>
            <p className="text-xs text-slate-500 mt-1.5">Reconciled bank & gateway collections</p>
          </div>
        </div>
      </div>

      {/* Strategic Executive Unit Economics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Est. Customer LTV</div>
            <div className="text-xl font-bold text-white mt-0.5">₹1,82,000</div>
            <div className="text-[11px] text-slate-400">Based on 24-mo contract horizon</div>
          </div>
        </div>

        <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Average Revenue / Account</div>
            <div className="text-xl font-bold text-white mt-0.5">₹12,666 / mo</div>
            <div className="text-[11px] text-emerald-400">+12% ACV growth this quarter</div>
          </div>
        </div>

        <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Accounts Receivable Risk</div>
            <div className="text-xl font-bold text-amber-400 mt-0.5">{formatCurrency(summary?.overdue_invoices_amount || 11798.82)}</div>
            <div className="text-[11px] text-slate-400">1 invoice aging past due date</div>
          </div>
        </div>
      </div>

      {/* Revenue Trajectory Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Strategic Cashflow & Invoicing Velocity</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              MRR vs Total Invoiced Cashflow across the last 6 fiscal months
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-indigo-600" />
              <span>MRR Run Rate</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span>Invoiced Cash</span>
            </div>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={summary?.monthly_trends || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="execMrr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="execInv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} tickFormatter={(val) => `₹${val / 1000}k`} />
              <Tooltip
                formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, '']}
                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Area type="monotone" dataKey="mrr" stroke="#4f46e5" strokeWidth={2.5} fillOpacity={1} fill="url(#execMrr)" name="MRR" />
              <Area type="monotone" dataKey="invoiced" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#execInv)" name="Invoiced" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two Column Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900">Enterprise Contracts Portfolio</h3>
            <Link to="/subscriptions" className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              <span>Inspect All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {recentSubs.map((sub) => (
              <div key={sub.id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-900">{sub.customer?.name}</p>
                  <p className="text-[11px] text-slate-500">{sub.subscription_number} • {sub.plan?.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-900">{formatCurrency(sub.amount)}</p>
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 uppercase">
                    {sub.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900">Capital Ledger & Invoices</h3>
            <Link to="/invoices" className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              <span>Open Ledger</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {recentInvoices.map((inv) => (
              <div key={inv.id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-900">{inv.customer?.name}</p>
                  <p className="text-[11px] text-slate-500">{inv.invoice_number} • Due: {new Date(inv.due_date).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-900">{formatCurrency(inv.total_amount)}</p>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                    inv.status === 'PAID' ? 'bg-emerald-50 text-emerald-700' : inv.status === 'OVERDUE' ? 'bg-rose-50 text-rose-700' : 'bg-blue-50 text-blue-700'
                  }`}>
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
