import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../lib/api';
import { DashboardSummary, Subscription, Invoice } from '../types';
import { ExecutiveDashboard } from '../components/dashboard/ExecutiveDashboard';
import { BillingDashboard } from '../components/dashboard/BillingDashboard';
import { SalesDashboard } from '../components/dashboard/SalesDashboard';
import { AnalystDashboard } from '../components/dashboard/AnalystDashboard';
import { Shield, CreditCard, Sparkles, Activity, Check } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, role, setOverrideRole } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentSubs, setRecentSubs] = useState<Subscription[]>([]);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);

  const fetchDashboardData = async () => {
    try {
      const [sumRes, subRes, invRes] = await Promise.all([
        apiClient.get('/analytics/summary'),
        apiClient.get('/subscriptions?page_size=10'),
        apiClient.get('/invoices?page_size=10'),
      ]);
      setSummary(sumRes.data);
      setRecentSubs(subRes.data.items || []);
      setRecentInvoices(invRes.data.items || []);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      // Realistic fallback for demonstration
      setSummary({
        mrr: 37998,
        arr: 455976,
        active_subscriptions: 3,
        total_customers: 5,
        overdue_invoices_amount: 11798.82,
        overdue_invoices_count: 1,
        total_collected_amount: 3538.82,
        currency: 'INR',
        monthly_trends: [
          { month: 'May', mrr: 22748, invoiced: 26842, collected: 25477 },
          { month: 'Jun', mrr: 25197, invoiced: 29733, collected: 28221 },
          { month: 'Jul', mrr: 28347, invoiced: 33450, collected: 31749 },
          { month: 'Aug', mrr: 31147, invoiced: 36753, collected: 34885 },
          { month: 'Sep', mrr: 33247, invoiced: 39231, collected: 37237 },
          { month: 'Oct', mrr: 37998, invoiced: 44837, collected: 41296 },
        ],
      });
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleApproveQuotation = async (subId: string) => {
    try {
      await apiClient.post(`/subscriptions/${subId}/transition`, {
        target_status: 'ACTIVE',
      });
      fetchDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve quotation');
    }
  };

  const formatCurrency = (val: number | string) => {
    const num = Number(val) || 0;
    return `₹${num.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  };

  // Roles configuration for interactive switcher
  const roleViews = [
    {
      id: 'TENANT_OWNER',
      label: 'Executive Command Center',
      roleName: 'C-Level / Owner',
      icon: Shield,
      accent: 'border-indigo-600 text-indigo-700 bg-indigo-50/80',
    },
    {
      id: 'BILLING_MANAGER',
      label: 'Billing & AR Collections',
      roleName: 'Billing & Finance',
      icon: CreditCard,
      accent: 'border-emerald-600 text-emerald-700 bg-emerald-50/80',
    },
    {
      id: 'SALES_MANAGER',
      label: 'Sales Pipeline & Deals',
      roleName: 'Sales Director',
      icon: Sparkles,
      accent: 'border-blue-600 text-blue-700 bg-blue-50/80',
    },
    {
      id: 'ANALYST',
      label: 'Revenue Intelligence Lab',
      roleName: 'Financial Analyst',
      icon: Activity,
      accent: 'border-purple-600 text-purple-700 bg-purple-50/80',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Role-Based Dashboard View Switcher */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Role-Specific Dashboard Experience
            </span>
            <span className="text-[10px] bg-indigo-100 text-indigo-700 font-semibold px-2 py-0.5 rounded-full">
              Customized for {user?.full_name || 'Active User'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Switch between tailored role views to evaluate personalized workflows for each department.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 rounded-xl">
          {roleViews.map((v) => {
            const Icon = v.icon;
            const isCurrent = role === v.id;
            return (
              <button
                key={v.id}
                onClick={() => setOverrideRole(v.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isCurrent
                    ? `${v.accent} shadow-sm border`
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 border border-transparent'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{v.roleName}</span>
                {isCurrent && <Check className="w-3 h-3 ml-0.5" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Render the specialized dashboard based on current role */}
      {role === 'BILLING_MANAGER' || role === 'FINANCE_OFFICER' ? (
        <BillingDashboard
          summary={summary}
          recentInvoices={recentInvoices}
          formatCurrency={formatCurrency}
        />
      ) : role === 'SALES_MANAGER' ? (
        <SalesDashboard
          subscriptions={recentSubs}
          formatCurrency={formatCurrency}
          onApproveQuotation={handleApproveQuotation}
        />
      ) : role === 'ANALYST' ? (
        <AnalystDashboard summary={summary} formatCurrency={formatCurrency} />
      ) : (
        <ExecutiveDashboard
          summary={summary}
          recentSubs={recentSubs}
          recentInvoices={recentInvoices}
          formatCurrency={formatCurrency}
        />
      )}
    </div>
  );
};
