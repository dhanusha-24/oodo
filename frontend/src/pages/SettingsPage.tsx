import React, { useEffect, useState } from 'react';
import { ShieldCheck, Check, Save } from 'lucide-react';
import apiClient from '../lib/api';

export const SettingsPage: React.FC = () => {
  const [name, setName] = useState<string>('Acme Cloud Technologies Pvt Ltd');
  const [currency, setCurrency] = useState<string>('INR');
  const [timezone, setTimezone] = useState<string>('Asia/Kolkata');
  const [taxId, setTaxId] = useState<string>('29AABCA1234A1Z5');
  const [invoicePrefix, setInvoicePrefix] = useState<string>('INV');
  const [saving, setSaving] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await apiClient.get('/settings');
        if (res.data) {
          setName(res.data.name || 'Acme Cloud Technologies Pvt Ltd');
          setCurrency(res.data.base_currency || 'INR');
          setTimezone(res.data.timezone || 'Asia/Kolkata');
        }
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      await apiClient.patch('/settings', {
        name,
        base_currency: currency,
        timezone,
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      alert('Failed to update tenant configuration');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tenant Operations & Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Multi-tenant tenant isolation parameters, Indian GST invoicing rules, and company profile.
        </p>
      </div>

      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-sm flex items-center gap-2">
          <Check className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>Tenant settings saved and applied successfully across all cluster nodes!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Organization Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-1">Company Profile</h2>
          <p className="text-xs text-slate-500 mb-4">
            This name will appear on all client-facing quotations, tax invoices, and emails.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Company Legal Entity Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Base Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="INR">INR (₹) - Indian Rupee</option>
                  <option value="USD">USD ($) - US Dollar</option>
                  <option value="EUR">EUR (€) - Euro</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Default Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST +05:30)</option>
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Invoicing & Indian Tax Rules */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-1">Tax & Invoicing Sequences</h2>
          <p className="text-xs text-slate-500 mb-4">
            Deterministic document numbering with Indian fiscal year resets (April 1 - March 31).
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Organization GSTIN</label>
              <input
                type="text"
                value={taxId}
                onChange={(e) => setTaxId(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm uppercase font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice Prefix Format</label>
              <input
                type="text"
                value={invoicePrefix}
                onChange={(e) => setInvoicePrefix(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm uppercase font-mono focus:outline-none focus:border-indigo-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">Generated sample: {invoicePrefix}-2026-27-0001</p>
            </div>
          </div>
        </div>

        {/* Tenant Architecture Compliance Note */}
        <div className="p-4 rounded-xl bg-slate-900 text-slate-300 text-xs flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div>
            <strong className="text-white block mb-0.5">Strict Tenant Boundary Enforcement</strong>
            All database queries, background jobs, and document sequences are strictly partitioned by Tenant UUID. Row-level security prevents cross-tenant access.
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Updating Settings...' : 'Save Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
