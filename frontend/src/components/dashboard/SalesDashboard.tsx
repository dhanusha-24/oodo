import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Plus,
  CheckCircle,
  Clock,
  Sparkles,
  TrendingUp,
  Target,
  BadgeCheck,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Subscription } from '../../types';

interface SalesDashboardProps {
  subscriptions: Subscription[];
  formatCurrency: (val: number | string) => string;
  onApproveQuotation: (subId: string) => void;
}

export const SalesDashboard: React.FC<SalesDashboardProps> = ({
  subscriptions,
  formatCurrency,
  onApproveQuotation,
}) => {
  // Funnel data
  const funnelData = [
    { stage: 'Prospects', count: 12, value: '₹5,50,000' },
    { stage: 'Quotations', count: 5, value: '₹1,45,000' },
    { stage: 'Confirmed', count: 3, value: '₹95,000' },
    { stage: 'Active Won', count: 3, value: '₹37,998' },
  ];

  const pendingQuotations = subscriptions.filter(
    (s) => s.status === 'QUOTATION' || s.status === 'CONFIRMED'
  );

  const pipelineValue = subscriptions.reduce((acc, curr) => acc + Number(curr.amount), 0);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Sales Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 border border-blue-800/40 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Sales Director Deal Velocity Cockpit</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Contract Pipeline & Deal Conversions</h1>
            <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl">
              Monitor active quotes, customer contract approvals, and expansion opportunities across enterprise accounts.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/subscriptions"
              className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-600/30 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Draft New Quotation</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Sales KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Contract Pipeline
            </span>
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">{formatCurrency(pipelineValue)}</h3>
            <p className="text-xs text-blue-600 mt-1.5 font-medium">Across {subscriptions.length} enterprise deals</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Pending Quote Approval
            </span>
            <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-amber-600">
              {pendingQuotations.length} Deals
            </h3>
            <p className="text-xs text-slate-500 mt-1.5">Awaiting customer or sales signoff</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Quote-to-Close Rate
            </span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <BadgeCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-emerald-600">82.5%</h3>
            <p className="text-xs text-emerald-600 mt-1.5 font-medium">+6.4% improvement this cycle</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Avg Contract Value (ACV)
            </span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Target className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              {formatCurrency(pipelineValue / (subscriptions.length || 1))}
            </h3>
            <p className="text-xs text-slate-500 mt-1.5">Weighted average per subscriber</p>
          </div>
        </div>
      </div>

      {/* Deal Velocity Funnel Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Contract Funnel Stage Conversion</h3>
            <p className="text-xs text-slate-500 mt-0.5">Pipeline progression from prospect discovery to active contract</p>
          </div>
          <span className="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-lg font-semibold">
            High Velocity
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={funnelData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="stage" stroke="#64748b" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
              <Tooltip
                formatter={(val: any) => [`${val} Deals`, 'Count']}
                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} barSize={44} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Actionable Deals Pending Closing */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Quotations & Contracts In Negotiation</h3>
            <p className="text-xs text-slate-500">Fast-track high priority contracts directly into active subscription billing</p>
          </div>
          <Link to="/subscriptions" className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1">
            <span>All Contracts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {pendingQuotations.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No quotations pending approval.</p>
          ) : (
            pendingQuotations.map((sub) => (
              <div key={sub.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900 text-sm">{sub.customer?.name}</span>
                    <span className="font-mono text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                      {sub.subscription_number}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Tier: <strong>{sub.plan?.name}</strong> • Value: <strong>{formatCurrency(sub.amount)}</strong>/{sub.billing_interval.toLowerCase()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full font-semibold uppercase bg-amber-50 text-amber-700 border border-amber-200">
                    {sub.status}
                  </span>
                  <button
                    onClick={() => onApproveQuotation(sub.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Approve & Activate Deal</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
