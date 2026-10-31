import React, { useEffect, useState } from 'react';
import {
  Plus,
  CheckCircle,
  AlertCircle,
  XCircle,
  Clock,
  X,
} from 'lucide-react';
import apiClient from '../lib/api';
import { Customer, Plan, Subscription } from '../types';

export const SubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Form state
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('');
  const [selectedPlanId, setSelectedPlanId] = useState<string>('');
  const [initialStatus, setInitialStatus] = useState<string>('ACTIVE');
  const [billingInterval, setBillingInterval] = useState<'MONTHLY' | 'ANNUAL'>('MONTHLY');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const url = statusFilter === 'ALL' ? '/subscriptions?page_size=50' : `/subscriptions?status=${statusFilter}&page_size=50`;
      const [subRes, custRes, planRes] = await Promise.all([
        apiClient.get(url),
        apiClient.get('/customers?page_size=100'),
        apiClient.get('/plans'),
      ]);
      setSubscriptions(subRes.data.items || []);
      setCustomers(custRes.data.items || []);
      setPlans(planRes.data || []);
      if (custRes.data.items?.length > 0 && !selectedCustomerId) {
        setSelectedCustomerId(custRes.data.items[0].id);
      }
      if (planRes.data?.length > 0 && !selectedPlanId) {
        setSelectedPlanId(planRes.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load subscriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiClient.post('/subscriptions', {
        customer_id: selectedCustomerId,
        plan_id: selectedPlanId,
        billing_interval: billingInterval,
        initial_status: initialStatus,
        auto_renew: true,
      });
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create subscription');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransition = async (subId: string, targetStatus: string, reason?: string) => {
    try {
      await apiClient.post(`/subscriptions/${subId}/transition`, {
        target_status: targetStatus,
        reason: reason || undefined,
      });
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update subscription status');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3" />
            <span>ACTIVE</span>
          </span>
        );
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Clock className="w-3 h-3" />
            <span>CONFIRMED</span>
          </span>
        );
      case 'QUOTATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3" />
            <span>QUOTATION</span>
          </span>
        );
      case 'CANCELLED':
      case 'CLOSED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
            <XCircle className="w-3 h-3" />
            <span>{status}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscription Lifecycles</h1>
          <p className="text-sm text-slate-500 mt-1">
            Automate B2B contracts, state machines (Draft &rarr; Quotation &rarr; Confirmed &rarr; Active), and recurring invoicing.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Subscription</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-xs font-semibold">
        {['ALL', 'ACTIVE', 'CONFIRMED', 'QUOTATION', 'CANCELLED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === st
                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase font-semibold">
                <th className="py-3 px-5">Subscription #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Tier & Price</th>
                <th className="py-3 px-4">Billing Cycle</th>
                <th className="py-3 px-4 text-center">Lifecycle Status</th>
                <th className="py-3 px-5 text-right">State Machine Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    Loading subscriptions...
                  </td>
                </tr>
              ) : subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    No subscriptions found for this filter.
                  </td>
                </tr>
              ) : (
                subscriptions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-5 font-mono font-medium text-indigo-600">
                      {sub.subscription_number}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {sub.customer?.name || 'Customer Account'}
                    </td>
                    <td className="py-3.5 px-4 text-xs">
                      <span className="font-semibold text-slate-800">{sub.plan?.name || 'Plan'}</span>
                      <div className="text-slate-500">
                        ₹{Number(sub.amount).toLocaleString('en-IN')}/{sub.billing_interval === 'ANNUAL' ? 'yr' : 'mo'}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500">
                      {new Date(sub.start_date).toLocaleDateString()} &rarr;{' '}
                      {sub.current_period_end ? new Date(sub.current_period_end).toLocaleDateString() : 'Active'}
                    </td>
                    <td className="py-3.5 px-4 text-center">{getStatusBadge(sub.status)}</td>
                    <td className="py-3.5 px-5 text-right">
                      {sub.status === 'QUOTATION' && (
                        <button
                          onClick={() => handleTransition(sub.id, 'CONFIRMED')}
                          className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors"
                        >
                          Approve Quotation
                        </button>
                      )}
                      {sub.status === 'CONFIRMED' && (
                        <button
                          onClick={() => handleTransition(sub.id, 'ACTIVE')}
                          className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg border border-emerald-200 transition-colors"
                        >
                          Activate & Bill
                        </button>
                      )}
                      {sub.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleTransition(sub.id, 'CANCELLED', 'Customer requested cancellation')}
                          className="px-2.5 py-1 text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg border border-rose-200 transition-colors"
                        >
                          Cancel
                        </button>
                      )}
                      {(sub.status === 'CANCELLED' || sub.status === 'CLOSED') && (
                        <span className="text-xs text-slate-400 italic">Terminated</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Subscription Wizard Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Create Subscription Contract</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubscription} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Customer *</label>
                <select
                  required
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.tax_id || 'No GSTIN'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Plan *</label>
                <select
                  required
                  value={selectedPlanId}
                  onChange={(e) => setSelectedPlanId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — ₹{Number(p.price).toLocaleString('en-IN')}/{p.billing_interval.toLowerCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Billing Interval</label>
                  <select
                    value={billingInterval}
                    onChange={(e) => setBillingInterval(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="MONTHLY">Monthly</option>
                    <option value="ANNUAL">Annual</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Status</label>
                  <select
                    value={initialStatus}
                    onChange={(e) => setInitialStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="ACTIVE">Active (Immediate Invoicing)</option>
                    <option value="QUOTATION">Quotation (Pending Approval)</option>
                    <option value="CONFIRMED">Confirmed</option>
                    <option value="DRAFT">Draft</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Contract'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
