import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight, Zap, AlertCircle, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface TestAccount {
  label: string;
  role: string;
  email: string;
  tenant: string;
}

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState<string>('owner@acme.com');
  const [password, setPassword] = useState<string>('SecurePassword123!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { login, demoLogin } = useAuth();
  const navigate = useNavigate();

  const testAccounts: TestAccount[] = [
    { label: 'Acme Admin', role: 'Tenant Owner', email: 'owner@acme.com', tenant: 'Acme Cloud' },
    { label: 'Billing Manager', role: 'Invoicing & Pay', email: 'billing@acme.com', tenant: 'Acme Cloud' },
    { label: 'Sales Director', role: 'Contracts & CRM', email: 'sales@acme.com', tenant: 'Acme Cloud' },
    { label: 'Financial Analyst', role: 'MRR & Reports', email: 'analyst@acme.com', tenant: 'Acme Cloud' },
    { label: 'Starlight Admin', role: 'Tenant 2 (Isolation)', email: 'admin@starlight.io', tenant: 'Starlight Digital' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (accEmail: string) => {
    setEmail(accEmail);
    setPassword('SecurePassword123!');
    setError(null);
    setLoading(true);
    try {
      await login(accEmail, 'SecurePassword123!');
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to authenticate');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setError(null);
    setLoading(true);
    try {
      await demoLogin();
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to login with demo credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      {/* Background glowing gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-lg relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-2xl mx-auto flex items-center justify-center text-white shadow-xl shadow-indigo-500/25 mb-4">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Multi-Tenant Subscription Hub</h1>
          <p className="text-slate-400 text-sm mt-1">
            B2B SaaS Subscription Lifecycle & GST Billing Engine
          </p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
          {/* Quick Demo Button */}
          <div className="mb-5 p-4 rounded-xl bg-gradient-to-r from-indigo-950 to-violet-950 border border-indigo-700/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                Hackathon Submission Mode
              </span>
              <span className="text-[10px] bg-indigo-500/30 text-indigo-200 px-2 py-0.5 rounded font-mono">
                1-Click
              </span>
            </div>
            <p className="text-xs text-slate-300 mb-3">
              Instantly log in as <strong>Acme Admin</strong> with pre-seeded customers, plans & invoices.
            </p>
            <button
              onClick={handleDemo}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
            >
              <span>Instant Acme Admin Login</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Test Account Picker */}
          <div className="mb-6">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
              <Users className="w-3.5 h-3.5 text-indigo-400" />
              <span>Available Test Accounts (Click to Login)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {testAccounts.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => handleQuickLogin(acc.email)}
                  disabled={loading}
                  className="text-left p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/60 hover:bg-slate-800/80 transition-all text-xs group"
                >
                  <div className="font-semibold text-slate-200 group-hover:text-indigo-300 flex items-center justify-between">
                    <span>{acc.label}</span>
                    <span className="text-[10px] text-slate-500 font-normal">{acc.tenant}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate mt-0.5">{acc.email}</div>
                  <div className="text-[10px] text-indigo-400/80 font-mono mt-0.5">{acc.role}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="relative flex py-1 items-center mb-5">
            <div className="flex-grow border-t border-slate-800" />
            <span className="flex-shrink mx-3 text-xs text-slate-500 uppercase">Or manual password login</span>
            <div className="flex-grow border-t border-slate-800" />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Work Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                placeholder="••••••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-lg transition-colors border border-slate-700 disabled:opacity-50 mt-2"
            >
              {loading ? 'Authenticating...' : 'Sign In with Password'}
            </button>
          </form>
        </div>

        <div className="text-center mt-6 text-xs text-slate-500">
          Default Password for all test accounts: <code className="text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded font-mono">SecurePassword123!</code>
        </div>
      </div>
    </div>
  );
};
