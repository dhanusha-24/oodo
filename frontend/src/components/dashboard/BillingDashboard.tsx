import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  CreditCard,
  AlertTriangle,
  ArrowRight,
  Plus,
  Clock,
  Percent,
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
import { DashboardSummary, Invoice } from '../../types';

interface DashboardProps {
  summary: DashboardSummary | null;
  recentInvoices: Invoice[];
  formatCurrency: (val: number | string) => string;
}

export const BillingDashboard: React.FC<DashboardProps> = ({
  summary,
  recentInvoices,
  formatCurrency,
}) => {
  // Aging analysis data
  const agingData = [
    { bucket: 'Current (0-15d)', amount: 15337, count: 2 },
    { bucket: 'Due (16-30d)', amount: 7850, count: 1 },
    { bucket: 'Overdue (31-60d)', amount: 11798.82, count: 1 },
    { bucket: 'Critical (>60d)', amount: 0, count: 0 },
  ];

  const overdueInvoices = recentInvoices.filter(
    (i) => i.status === 'OVERDUE' || i.status === 'PARTIALLY_PAID' || Number(i.balance_due) > 0
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Billing Operational Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950 via-slate-900 to-slate-950 border border-emerald-800/40 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-semibold mb-3">
              <FileText className="w-3.5 h-3.5" />
              <span>Financial Operations & Billing Console</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Accounts Receivable & Collections Hub</h1>
            <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl">
              Indian GST invoicing (SAC 998313), automated payment reconciliation ledger, and AR aging buckets.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              to="/invoices"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/30 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Issue Tax Invoice</span>
            </Link>
            <Link
              to="/payments"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all"
            >
              <CreditCard className="w-4 h-4" />
              <span>Record Offline Receipt</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Financial Operations KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Cash Realized (MTD)
            </span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CreditCard className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">
              {formatCurrency(summary?.total_collected_amount || 3538.82)}
            </h3>
            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-emerald-600 font-medium">
              <span>Razorpay & NEFT Bank cleared</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Outstanding Receivables
            </span>
            <div className="w-9 h-9 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-rose-600">
              {formatCurrency(summary?.overdue_invoices_amount || 11798.82)}
            </h3>
            <p className="text-xs text-rose-700 mt-1.5 font-medium">{summary?.overdue_invoices_count || 1} Invoice in Aging Queue</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Days Sales Outstanding (DSO)
            </span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">11.4 Days</h3>
            <p className="text-xs text-emerald-600 mt-1.5 font-medium">Industry Benchmark: &lt; 30 Days</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              GST Tax Liability (18%)
            </span>
            <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Percent className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">₹6,299.50</h3>
            <p className="text-xs text-slate-500 mt-1.5">SAC 998313 • Indian GST return</p>
          </div>
        </div>
      </div>

      {/* AR Aging Analysis Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Accounts Receivable Aging Buckets</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Breakdown of pending receivables categorized by payment term overdue thresholds
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-lg font-medium">
              Net 14 Days Default Term
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={agingData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="bucket" stroke="#64748b" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} tickFormatter={(val) => `₹${val / 1000}k`} />
              <Tooltip
                formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Balance Due']}
                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Bar dataKey="amount" fill="#10b981" radius={[6, 6, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Actionable Receivables Collection Queue */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Critical Collections Queue (Pending & Overdue)</h3>
            <p className="text-xs text-slate-500">Invoices requiring immediate payment follow-up or reconciliation</p>
          </div>
          <Link to="/invoices" className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
            <span>View All Invoices</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold">
                <th className="py-2.5 px-4">Invoice #</th>
                <th className="py-2.5 px-4">Client / GSTIN</th>
                <th className="py-2.5 px-4">Due Date</th>
                <th className="py-2.5 px-4 text-right">Invoice Value</th>
                <th className="py-2.5 px-4 text-right">Balance Due</th>
                <th className="py-2.5 px-4 text-center">Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {overdueInvoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">All client balances settled!</td>
                </tr>
              ) : (
                overdueInvoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/70">
                    <td className="py-3 px-4 font-mono font-semibold text-indigo-600">{inv.invoice_number}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{inv.customer?.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{inv.customer?.tax_id || 'URP'}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-500">{new Date(inv.due_date).toLocaleDateString()}</td>
                    <td className="py-3 px-4 text-right font-medium">{formatCurrency(inv.total_amount)}</td>
                    <td className="py-3 px-4 text-right font-bold text-rose-600">{formatCurrency(inv.balance_due)}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        inv.status === 'OVERDUE' ? 'bg-rose-50 text-rose-700' : 'bg-purple-50 text-purple-700'
                      }`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to="/payments"
                        className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold rounded-lg border border-indigo-200 transition-colors"
                      >
                        Record Receipt
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
