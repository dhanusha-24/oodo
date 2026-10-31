import React from 'react';
import {
  TrendingUp,
  Percent,
  Download,
  Activity,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { DashboardSummary } from '../../types';

interface AnalystDashboardProps {
  summary: DashboardSummary | null;
  formatCurrency: (val: number | string) => string;
}

export const AnalystDashboard: React.FC<AnalystDashboardProps> = ({
  summary,
  formatCurrency,
}) => {
  // Plan mix data
  const tierDistribution = [
    { tier: 'Starter Tier', subscribers: 2, mrr: 5998, percentage: 16 },
    { tier: 'Professional', subscribers: 2, mrr: 19998, percentage: 53 },
    { tier: 'Enterprise', subscribers: 1, mrr: 12000, percentage: 31 },
  ];

  const handleExportCSV = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Monthly Recurring Revenue (MRR)', summary?.mrr || 37998],
      ['Annual Run Rate (ARR)', summary?.arr || 455976],
      ['Net Revenue Retention (NRR)', '118%'],
      ['Active Subscriptions', summary?.active_subscriptions || 3],
      ['Accounts Receivable Aging', summary?.overdue_invoices_amount || 11798.82],
      ['Total Realized Cash', summary?.total_collected_amount || 3538.82],
    ];
    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'saas_financial_telemetry.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Analyst Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-950 via-slate-900 to-indigo-950 border border-purple-800/40 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-300 text-xs font-semibold mb-3">
              <Activity className="w-3.5 h-3.5" />
              <span>Revenue Intelligence & SaaS Telemetry Lab</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Cohort Retention & Unit Economics</h1>
            <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl">
              Deep-dive cohort telemetry, Net Revenue Retention (NRR), tier contribution matrices, and cash conversion cycles.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExportCSV}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-purple-600/30 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Export Telemetry (CSV)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Analyst KPI Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Net Revenue Retention (NRR)
            </span>
            <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Percent className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-purple-600">118.2%</h3>
            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-emerald-600 font-medium">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>Expansion outpaces churn</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              CAC Payback Horizon
            </span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">4.2 Months</h3>
            <p className="text-xs text-emerald-600 mt-1.5 font-medium">Top-quartile B2B benchmark</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              LTV : CAC Ratio
            </span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-emerald-600">5.8x</h3>
            <p className="text-xs text-slate-500 mt-1.5">Healthy unit economic return</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Gross Software Margin
            </span>
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">86.4%</h3>
            <p className="text-xs text-slate-500 mt-1.5">Cloud infrastructure cost deducted</p>
          </div>
        </div>
      </div>

      {/* Multi-Line Cohort Velocity Telemetry Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Multi-Channel Telemetry: MRR vs Invoiced vs Collected</h3>
            <p className="text-xs text-slate-500 mt-0.5">Comparative 6-month growth velocity across all revenue stages</p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="text-purple-600 font-semibold">• MRR Target</span>
            <span className="text-indigo-600 font-semibold">• Invoiced</span>
            <span className="text-emerald-600 font-semibold">• Realized Cash</span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={summary?.monthly_trends || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} tickFormatter={(val) => `₹${val / 1000}k`} />
              <Tooltip
                formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, '']}
                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend />
              <Line type="monotone" dataKey="mrr" stroke="#9333ea" strokeWidth={3} name="MRR" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="invoiced" stroke="#4f46e5" strokeWidth={2.5} name="Invoiced Cash" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="collected" stroke="#10b981" strokeWidth={2.5} name="Realized Cash" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tier Breakdown Matrix */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Subscription Tier Contribution Analysis</h3>
            <p className="text-xs text-slate-500">Distribution of monthly revenue and active subscriber density by pricing plan</p>
          </div>
          <span className="text-xs bg-purple-50 text-purple-700 px-3 py-1 rounded-lg font-medium">
            3 Active Pricing Packages
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tierDistribution.map((t) => (
            <div key={t.tier} className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">{t.tier}</span>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                  {t.percentage}% of MRR
                </span>
              </div>
              <div className="text-xl font-extrabold text-slate-900 mt-2">{formatCurrency(t.mrr)}</div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-3">
                <div className="bg-purple-600 h-full rounded-full" style={{ width: `${t.percentage}%` }} />
              </div>
              <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                <span>{t.subscribers} Accounts subscribed</span>
                <span>Avg: ₹{(t.mrr / t.subscribers).toLocaleString()}/sub</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
