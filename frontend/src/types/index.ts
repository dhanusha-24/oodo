export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role?: string;
}

export interface Tenant {
  id: string;
  name: string;
  timezone: string;
  base_currency: string;
  settings_json?: Record<string, any>;
}

export interface CustomerContact {
  id?: string;
  name: string;
  email?: string;
  phone?: string;
  role?: string;
  is_primary: boolean;
}

export interface Customer {
  id: string;
  tenant_id: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  billing_address_line1?: string;
  billing_city?: string;
  billing_state?: string;
  billing_postal_code?: string;
  billing_country: string;
  tax_id?: string;
  currency_preference: string;
  payment_terms_days: number;
  status: string;
  notes?: string;
  external_id?: string;
  outstanding_balance: number | string;
  created_at: string;
  contacts?: CustomerContact[];
}

export interface Plan {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  description?: string;
  billing_interval: 'MONTHLY' | 'ANNUAL';
  price: number | string;
  currency: string;
  trial_days: number;
  is_active: boolean;
  features_list?: string;
  created_at: string;
}

export interface Subscription {
  id: string;
  tenant_id: string;
  customer_id: string;
  plan_id: string;
  subscription_number: string;
  status: 'DRAFT' | 'QUOTATION' | 'CONFIRMED' | 'ACTIVE' | 'PAUSED' | 'CANCELLED' | 'CLOSED';
  start_date: string;
  end_date?: string;
  current_period_start?: string;
  current_period_end?: string;
  amount: number | string;
  currency: string;
  billing_interval: 'MONTHLY' | 'ANNUAL';
  auto_renew: boolean;
  cancellation_reason?: string;
  created_at: string;
  customer?: Customer;
  plan?: Plan;
}

export interface Invoice {
  id: string;
  tenant_id: string;
  customer_id: string;
  subscription_id?: string;
  invoice_number: string;
  status: 'DRAFT' | 'ISSUED' | 'PAID' | 'PARTIALLY_PAID' | 'OVERDUE' | 'VOID';
  issue_date: string;
  due_date: string;
  subtotal: number | string;
  tax_rate: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  amount_paid: number | string;
  balance_due: number | string;
  currency: string;
  notes?: string;
  created_at: string;
  customer?: Customer;
}

export interface Payment {
  id: string;
  tenant_id: string;
  customer_id: string;
  invoice_id?: string;
  payment_number: string;
  amount: number | string;
  currency: string;
  payment_method: 'RAZORPAY' | 'BANK_TRANSFER' | 'STRIPE' | 'UPI' | 'CASH';
  status: 'SUCCESS' | 'PENDING' | 'FAILED';
  reference_id?: string;
  paid_at: string;
  notes?: string;
  created_at: string;
  customer?: Customer;
  invoice?: Invoice;
}

export interface MonthlyTrend {
  month: string;
  mrr: number;
  invoiced: number;
  collected: number;
}

export interface DashboardSummary {
  mrr: number;
  arr: number;
  active_subscriptions: number;
  total_customers: number;
  overdue_invoices_amount: number;
  overdue_invoices_count: number;
  total_collected_amount: number;
  currency: string;
  monthly_trends: MonthlyTrend[];
}
