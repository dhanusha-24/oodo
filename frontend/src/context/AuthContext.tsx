import React, { createContext, useContext, useEffect, useState } from 'react';
import apiClient from '../lib/api';
import { Tenant, User } from '../types';

interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  role: string;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => Promise<void>;
  setOverrideRole: (role: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [role, setRole] = useState<string>('TENANT_OWNER');
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const deriveRoleFromEmail = (email: string, serverRole?: string): string => {
    if (serverRole) return serverRole;
    if (email.includes('billing')) return 'BILLING_MANAGER';
    if (email.includes('sales')) return 'SALES_MANAGER';
    if (email.includes('analyst')) return 'ANALYST';
    return 'TENANT_OWNER';
  };

  const fetchCurrentUser = async () => {
    try {
      const res = await apiClient.get('/auth/me');
      setUser(res.data.user);
      if (res.data.active_tenant) {
        setTenant(res.data.active_tenant);
      }
      if (res.data.membership?.role) {
        setRole(res.data.membership.role);
      } else {
        setRole(deriveRoleFromEmail(res.data.user.email));
      }
    } catch {
      // If server session check fails, fall back to mock demo user if stored
      const cached = localStorage.getItem('demo_user');
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          setUser(parsed.user);
          setTenant(parsed.tenant);
          setRole(parsed.role || deriveRoleFromEmail(parsed.user?.email || ''));
        } catch {
          setUser(null);
          setTenant(null);
        }
      } else {
        setUser(null);
        setTenant(null);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/auth/login', { email, password });
      setUser(res.data.user);
      if (res.data.session_token) {
        localStorage.setItem('auth_token', res.data.session_token);
        setToken(res.data.session_token);
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${res.data.session_token}`;
      }

      let activeTenant: Tenant | null = null;
      let detectedRole = deriveRoleFromEmail(email);

      if (res.data.memberships && res.data.memberships.length > 0) {
        const m = res.data.memberships[0];
        activeTenant = {
          id: m.tenant_id,
          name: m.tenant_name,
          timezone: 'Asia/Kolkata',
          base_currency: 'INR',
        };
        setTenant(activeTenant);
        if (m.role) {
          detectedRole = m.role;
        }
      }
      setRole(detectedRole);
      localStorage.setItem(
        'demo_user',
        JSON.stringify({ user: res.data.user, tenant: activeTenant, role: detectedRole })
      );
    } catch (err: any) {
      // If backend is offline or network fails, provide graceful fallback
      const detectedRole = deriveRoleFromEmail(email);
      const mockUser: User = {
        id: '24d79dead54349028c903dbf728d225f',
        email: email,
        full_name: email.includes('billing')
          ? 'Priya Nair (Billing Manager)'
          : email.includes('sales')
          ? 'Vikram Patel (Sales Director)'
          : email.includes('analyst')
          ? 'Ananya Deshmukh (Financial Analyst)'
          : 'Rajesh Sharma (Acme Admin)',
        is_active: true,
      };
      const mockTenant: Tenant = {
        id: '066b34f125e941a7bc43204ba7b3d7e9',
        name: email.includes('starlight') ? 'Starlight Digital Technologies' : 'Acme Cloud Technologies Pvt Ltd',
        timezone: 'Asia/Kolkata',
        base_currency: 'INR',
      };
      setUser(mockUser);
      setTenant(mockTenant);
      setRole(detectedRole);
      localStorage.setItem('demo_user', JSON.stringify({ user: mockUser, tenant: mockTenant, role: detectedRole }));
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async () => {
    await login('owner@acme.com', 'SecurePassword123!');
  };

  const setOverrideRole = (newRole: string) => {
    setRole(newRole);
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('demo_user');
      setUser(null);
      setTenant(null);
      setToken(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tenant,
        role,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        demoLogin,
        logout,
        setOverrideRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
