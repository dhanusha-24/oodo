import React, { useEffect, useState } from 'react';
import { Check, Plus, Sparkles, X, AlertCircle } from 'lucide-react';
import apiClient from '../lib/api';
import { Plan } from '../types';

export const PlansPage: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Form State
  const [formName, setFormName] = useState<string>('');
  const [formCode, setFormCode] = useState<string>('');
  const [formPrice, setFormPrice] = useState<string>('');
  const [formInterval, setFormInterval] = useState<'MONTHLY' | 'ANNUAL'>('MONTHLY');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formFeatures, setFormFeatures] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/plans');
      setPlans(res.data || []);
    } catch (err) {
      console.error('Failed to load plans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiClient.post('/plans', {
        name: formName,
        code: formCode.toUpperCase(),
        description: formDescription || undefined,
        billing_interval: formInterval,
        price: parseFloat(formPrice) || 0,
        currency: 'INR',
        trial_days: 14,
        features_list: formFeatures || undefined,
      });
      setShowModal(false);
      setFormName('');
      setFormCode('');
      setFormPrice('');
      setFormDescription('');
      setFormFeatures('');
      fetchPlans();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create plan');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscription Plans & Tiers</h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure product packages, recurring intervals, and custom enterprise feature tiers.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Tier</span>
        </button>
      </div>

      {/* Plans Grid */}
      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">Loading plans...</div>
      ) : plans.length === 0 ? (
        <div className="py-12 text-center text-slate-400 text-sm">No plans configured yet.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const isPopular = plan.code === 'PRO';
            const features = plan.features_list
              ? plan.features_list.split(',').map((f) => f.trim())
              : ['Standard Cloud Access', 'Email SLA Support', 'Single Tenant Isolation'];

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl border transition-all duration-200 flex flex-col p-6 shadow-sm ${
                  isPopular
                    ? 'border-indigo-600 ring-2 ring-indigo-600/10 shadow-indigo-100/50 shadow-lg'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                {isPopular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1 shadow-sm">
                    <Sparkles className="w-3 h-3" />
                    <span>Most Popular</span>
                  </div>
                )}

                <div className="mb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-slate-900">{plan.name}</h3>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {plan.code}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5 min-h-[32px]">{plan.description}</p>
                </div>

                <div className="py-4 border-y border-slate-100 mb-6">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-slate-900">
                      ₹{Number(plan.price).toLocaleString('en-IN')}
                    </span>
                    <span className="text-xs text-slate-500">
                      /{plan.billing_interval === 'ANNUAL' ? 'year' : 'month'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">+ 18% GST Applicable (India SAC 998313)</p>
                </div>

                <div className="flex-1 space-y-3 mb-6">
                  <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Features Included</p>
                  <ul className="space-y-2 text-xs text-slate-600">
                    {features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-2">
                  <button
                    disabled
                    className="w-full py-2 px-4 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                  >
                    Active Plan (ID: {plan.code})
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Plan Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Create Subscription Tier</h2>
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

            <form onSubmit={handleCreatePlan} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tier Name *</label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. Scale Tier"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Code (Unique) *</label>
                  <input
                    type="text"
                    required
                    value={formCode}
                    onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                    placeholder="SCALE"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm uppercase font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Price (₹ INR) *</label>
                  <input
                    type="number"
                    required
                    value={formPrice}
                    onChange={(e) => setFormPrice(e.target.value)}
                    placeholder="14999"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Billing Interval</label>
                <select
                  value={formInterval}
                  onChange={(e) => setFormInterval(e.target.value as any)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="MONTHLY">Monthly</option>
                  <option value="ANNUAL">Annual</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="Short summary of this plan"
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Features (comma separated)</label>
                <textarea
                  value={formFeatures}
                  onChange={(e) => setFormFeatures(e.target.value)}
                  placeholder="50 Users, Priority SLA, Unlimited API"
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                />
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
                  {submitting ? 'Creating...' : 'Save Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
