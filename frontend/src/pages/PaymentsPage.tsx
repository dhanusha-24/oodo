import React, { useEffect, useState } from 'react';
import {
  Plus,
  CheckCircle,
  X,
  AlertCircle,
  ArrowDownLeft,
} from 'lucide-react';
import apiClient from '../lib/api';
import { Customer, Invoice, Payment } from '../types';

export const PaymentsPage: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [unpaidInvoices, setUnpaidInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Form State
  const [customerId, setCustomerId] = useState<string>('');
  const [invoiceId, setInvoiceId] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('BANK_TRANSFER');
  const [referenceId, setReferenceId] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [payRes, custRes, invRes] = await Promise.all([
        apiClient.get('/payments?page_size=50'),
        apiClient.get('/customers?page_size=100'),
        apiClient.get('/invoices?page_size=100'),
      ]);
      setPayments(payRes.data.items || []);
      setCustomers(custRes.data.items || []);
      const unpaid = (invRes.data.items || []).filter(
        (i: Invoice) => Number(i.balance_due) > 0
      );
      setUnpaidInvoices(unpaid);
      if (custRes.data.items?.length > 0 && !customerId) {
        setCustomerId(custRes.data.items[0].id);
      }
      if (unpaid.length > 0 && !invoiceId) {
        setInvoiceId(unpaid[0].id);
        setAmount(String(unpaid[0].balance_due));
      }
    } catch (err) {
      console.error('Failed to load payments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleInvoiceChange = (invId: string) => {
    setInvoiceId(invId);
    const inv = unpaidInvoices.find((i) => i.id === invId);
    if (inv) {
      setAmount(String(inv.balance_due));
      setCustomerId(inv.customer_id);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiClient.post('/payments', {
        customer_id: customerId,
        invoice_id: invoiceId || undefined,
        amount: parseFloat(amount) || 0,
        payment_method: paymentMethod,
        reference_id: referenceId || undefined,
        notes: notes || undefined,
      });
      setShowModal(false);
      setAmount('');
      setReferenceId('');
      setNotes('');
      fetchData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const totalCollected = payments.reduce(
    (acc, curr) => acc + (curr.status === 'SUCCESS' ? Number(curr.amount) : 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Payments & Collections</h1>
          <p className="text-sm text-slate-500 mt-1">
            Reconciliation ledger with Razorpay gateway, NEFT/RTGS bank transfers, and automatic invoice allocation.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Record Payment</span>
        </button>
      </div>

      {/* Summary KPI */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <ArrowDownLeft className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Realized Cash Collections
            </span>
            <h2 className="text-2xl font-extrabold text-slate-900 mt-0.5">
              ₹{totalCollected.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </h2>
          </div>
        </div>
        <div className="text-xs text-slate-500 font-medium bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">
          Automated double-entry reconciliation & balance updates enabled
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase font-semibold">
                <th className="py-3 px-5">Payment Receipt #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Allocated Invoice</th>
                <th className="py-3 px-4">Gateway / Method</th>
                <th className="py-3 px-4">Reference / UTR</th>
                <th className="py-3 px-4 text-right">Amount Paid</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-5 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 text-xs">
                    Loading payments ledger...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 text-xs">
                    No payments recorded yet.
                  </td>
                </tr>
              ) : (
                payments.map((pay) => (
                  <tr key={pay.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-5 font-mono font-semibold text-emerald-600">
                      {pay.payment_number}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {pay.customer?.name || 'Customer Account'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-indigo-600">
                      {pay.invoice?.invoice_number || 'Direct Payment'}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-700">
                      <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                        {pay.payment_method}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-500">
                      {pay.reference_id || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-slate-900">
                      ₹{Number(pay.amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle className="w-3 h-3" />
                        <span>{pay.status}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-right text-xs text-slate-400">
                      {new Date(pay.paid_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Payment Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Record Payment Received</h2>
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

            <form onSubmit={handleRecordPayment} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Invoice to Clear</label>
                <select
                  value={invoiceId}
                  onChange={(e) => handleInvoiceChange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="">No specific invoice (Unallocated)</option>
                  {unpaidInvoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} — {inv.customer?.name} (Due: ₹
                      {Number(inv.balance_due).toLocaleString('en-IN')})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer Account *</label>
                <select
                  required
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Amount (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="2999"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Method</label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="BANK_TRANSFER">Bank Transfer (NEFT/RTGS)</option>
                    <option value="RAZORPAY">Razorpay</option>
                    <option value="STRIPE">Stripe</option>
                    <option value="UPI">UPI</option>
                    <option value="CASH">Cash / Cheque</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reference / UTR / Gateway ID</label>
                <input
                  type="text"
                  value={referenceId}
                  onChange={(e) => setReferenceId(e.target.value)}
                  placeholder="e.g. UTR123456789"
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
                  {submitting ? 'Recording...' : 'Record Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
