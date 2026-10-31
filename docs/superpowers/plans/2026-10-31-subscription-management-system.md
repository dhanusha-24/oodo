# Subscription Management System (B2B SaaS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-tenant B2B subscription operations platform with strict state machine (`Draft -> Quotation -> Confirmed -> Active -> Closed`), immutable financial invoicing, discount controls, manual payment allocations, Celery-driven recurring billing, comprehensive analytics, and optional Gemini-powered operational insights.

**Architecture:** Monorepo with a React 19 + TypeScript + Vite SPA, a Python 3.12+ FastAPI backend, PostgreSQL 16+ for transactional ACID storage with tenant isolation, Redis + Celery 5 / Celery Beat for background billing and PDF rendering, MinIO for S3-compatible document storage, and Mailpit for email preview.

**Tech Stack:**
- **Frontend:** React 19, TypeScript, Vite, React Router v6, Tailwind CSS, shadcn/ui, Radix UI, TanStack Query, Axios, React Hook Form, Zod, TanStack Table, Recharts, Lucide React, date-fns.
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16+, Redis 7+, Celery 5 + Celery Beat, WeasyPrint + Jinja2, Argon2id (`pwdlib`), `google-genai` SDK.
- **Infrastructure & Testing:** Docker Compose, MinIO, Mailpit, pytest, pytest-asyncio, HTTPX, factory_boy, Vitest, Playwright, Locust.

**Spec Reference:**
- `Subscription_Management_System_Master_PRD.md` (Functional and domain baseline)
- `Subscription_Management_System_Developer_Spec-1.md` (Detailed API and data model specifications)
- `Subscription_Management_System_Tech_Stack.md` (Locked technology stack and architecture decisions)

---

## Global Constraints

- **Language / Framework:** Python 3.12+ for Backend, React 19 + TypeScript for Frontend.
- **Financial Precision:** Strict `Decimal` in Python, `NUMERIC(18, 4)` in DB. Canonical API outputs monetary values as formatted decimal strings (e.g. `"2124.00"`). Never use binary floating point.
- **Immutability:** Issued quotes and invoices are append-only and strictly immutable snapshots. Corrections are handled exclusively via Credit Notes / adjustments.
- **State Transitions:** Lifecycle `Draft -> Quotation -> Confirmed -> Active -> Closed` is server-enforced inside DB transactions with optimistic locking (`version`).
- **Multi-Tenancy:** Every tenant-owned table contains `tenant_id`. Every query and transaction enforces tenant membership and object ownership.
- **Timezone & Currency:** Default tenant timezone is `Asia/Kolkata` (stored in UTC, evaluated in tenant timezone). Default currency is `INR` (single currency per subscription, no FX conversion).
- **Billing Semantics:** In-advance billing on activation and each period anniversary. Anchor days on 29/30/31 clamped to end-of-month.
- **AI Boundaries:** Gemini AI is strictly advisory and read-only (explanations, search filters, help). Never execute raw LLM-generated SQL or permit LLM control over financial records.

---

## Review Focus

1. **Concurrent Billing Period Generation:** Worker retry or overlapping runs must never produce duplicate invoices for the same `(tenant_id, subscription_id, period_start, period_end, invoice_kind)`.
2. **Concurrent Discount Redemption Cap:** When 1 use remains on a capped discount, concurrent invoice issuances must atomically allow exactly one redemption without negative or overdrawn counters.
3. **Cross-Tenant Data Leakage:** Direct access to another tenant's customer, subscription, invoice, or quote ID must return 404 or 403, with zero cross-tenant query leaks.
4. **Payment Over-Allocation Race Condition:** Concurrent allocations across invoices must lock invoice balances and payment records transactionally, preventing allocation exceeding payment net value or invoice balance.
5. **Month-End Anchor Date Arithmetic:** Subscriptions created on Jan 31 must bill Feb 28 (or 29 on leap year) and restore March 31 without drifting forward to March 3.

---

## Phased Execution Roadmap

- **Phase 0:** Project Scaffolding, Monorepo Setup & Infrastructure Containers
- **Phase 1:** Core Data Architecture, Multi-Tenant Session Auth & RBAC
- **Phase 2:** Organization Settings, Customer Management & Versioned Plans Catalog
- **Phase 3:** Subscription Lifecycle Engine (`Draft -> Quotation -> Confirmed -> Active -> Closed`) & Quote PDF
- **Phase 4:** Deterministic Financial Calculation Engine, Tax Rules & Discount Engine
- **Phase 5:** Automated Billing Engine, Celery Schedules & Invoice PDF Generation
- **Phase 6:** Payment Ledger, Multi-Invoice Allocations, Reversals & Credit Notes
- **Phase 7:** Analytics Dashboard, Aging Buckets, Reporting Engine & CSV Exports
- **Phase 8:** Email Outbox Worker, Notification Center & Background Job Monitoring
- **Phase 9:** Gemini AI Gateway (Advisory Insights, Natural Language Filter, Help Assistant)
- **Phase 10:** Comprehensive QA Scenarios, 10k Seed Data & Locust Load Benchmark (<2s SLO)

---

## Detailed Task Breakdown

### Phase 0: Project Scaffolding & Infrastructure

#### Task 0.1: Monorepo & Container Scaffolding
**Files:**
- Create: `docker-compose.yml`
- Create: `backend/pyproject.toml`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/Dockerfile`
- Create: `.env.example`
- Create: `backend/app/main.py`

**Interfaces:**
- Consumes: Environment configuration.
- Produces: Running local stack: PostgreSQL 16 (`localhost:5432`), Redis 7 (`localhost:6379`), MinIO (`localhost:9000`), Mailpit (`localhost:8025`), FastAPI API (`localhost:8000`), Vite dev server (`localhost:5173`).

- [ ] **Step 1: Write `docker-compose.yml` with postgres, redis, minio, mailpit, backend, frontend, worker.**
- [ ] **Step 2: Create backend Python configuration using `uv`/`pyproject.toml` with FastAPI, SQLAlchemy, Alembic, Celery, Pydantic v2, WeasyPrint.**
- [ ] **Step 3: Create frontend configuration using Vite + React 19 + TypeScript + Tailwind CSS.**
- [ ] **Step 4: Verify containers start and healthcheck passes.**
  Run: `docker compose up -d postgres redis minio mailpit`
  Expected: Containers healthy.

---

### Phase 1: Core Data Architecture, Multi-Tenant Auth & RBAC

#### Task 1.1: Database Base Models & Alembic Configuration
**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/models/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Interfaces:**
- Produces: `Base` SQLAlchemy class with `tenant_id`, `created_at`, `updated_at`, `version` optimistic locking column, and async session factory.

- [ ] **Step 1: Write database connection manager supporting async PostgreSQL with psycopg/asyncpg.**
- [ ] **Step 2: Define `BaseModel` and `TenantScopedModel` with common columns.**
- [ ] **Step 3: Initialize Alembic and wire `target_metadata = Base.metadata`.**
- [ ] **Step 4: Run initial migration test:** `alembic check`.

#### Task 1.2: Tenants, Users, Memberships & Session Authentication
**Files:**
- Create: `backend/app/models/auth.py` (Tenant, User, Membership, UserSession, AuditLog)
- Create: `backend/app/core/security.py` (Argon2id hashing, session token crypto)
- Create: `backend/app/api/deps.py` (Current tenant, current user, role guards)
- Create: `backend/app/api/v1/auth.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/auth/login` (Sets HttpOnly session cookie, CSRF token header)
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - Roles: `TENANT_OWNER`, `SALES_MANAGER`, `BILLING_MANAGER`, `FINANCE_OFFICER`, `ANALYST`, `PLATFORM_ADMIN`

- [ ] **Step 1: Write failing test for user login, password verification, and session cookie generation.**
- [ ] **Step 2: Implement password hashing via Argon2id and session store with Redis / PostgreSQL fallback.**
- [ ] **Step 3: Implement tenant context resolution in FastAPI dependency injection (`get_current_tenant_user`).**
- [ ] **Step 4: Verify test passes.** `pytest backend/tests/test_auth.py -v`.

---

### Phase 2: Organization Settings, Customer Catalog & Versioned Plans

#### Task 2.1: Tenant Settings & Sequence Counters
**Files:**
- Create: `backend/app/models/tenant_sequence.py`
- Create: `backend/app/services/sequence_service.py`
- Create: `backend/app/api/v1/settings.py`
- Test: `backend/tests/test_sequence.py`

**Interfaces:**
- Produces: `SequenceService.get_next_number(tenant_id, doc_type, fiscal_year) -> str` (e.g. `INV-2026-27-000001` atomic reservation with row lock).

- [ ] **Step 1: Write test for atomic invoice sequence generation without numbers skipping or duplicates under concurrency.**
- [ ] **Step 2: Implement `tenant_sequences` table with `SELECT FOR UPDATE` atomic increment.**
- [ ] **Step 3: Implement Tenant settings API for timezone (`Asia/Kolkata` default), currency (`INR`), and payment terms.**
- [ ] **Step 4: Run sequence concurrency test.**

#### Task 2.2: Customer & Contact Management
**Files:**
- Create: `backend/app/models/customer.py` (Customer, CustomerContact)
- Create: `backend/app/schemas/customer.py`
- Create: `backend/app/services/customer_service.py`
- Create: `backend/app/api/v1/customers.py`
- Test: `backend/tests/test_customers.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/customers` (Paginated, filtered by search, status)
  - `POST /api/v1/customers`
  - `GET /api/v1/customers/{id}` (Includes outstanding balance and contact persons)
  - `PATCH /api/v1/customers/{id}`

- [ ] **Step 1: Write test for customer creation, unique external ID per tenant, and address validation.**
- [ ] **Step 2: Implement Customer domain models and repository.**
- [ ] **Step 3: Implement routes with server-side pagination (default 25, max 100).**
- [ ] **Step 4: Verify test passes.**

#### Task 2.3: Plans & Versioned Pricing Catalog
**Files:**
- Create: `backend/app/models/plan.py` (Plan, PlanVersion)
- Create: `backend/app/schemas/plan.py`
- Create: `backend/app/services/plan_service.py`
- Create: `backend/app/api/v1/plans.py`
- Test: `backend/tests/test_plans.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/plans`
  - `POST /api/v1/plans/{id}/versions` (Creates immutable plan version with `price`, `interval`, `currency`)
  - `GET /api/v1/plans`

- [ ] **Step 1: Write test ensuring plan price updates create a new version without modifying historical versions.**
- [ ] **Step 2: Implement Plan and PlanVersion models with unique `(tenant_id, code)`.**
- [ ] **Step 3: Implement PlanService.**
- [ ] **Step 4: Verify test passes.**

---

### Phase 3: Subscription State Machine & Quotation Lifecycle

#### Task 3.1: Subscription Core & State Machine
**Files:**
- Create: `backend/app/models/subscription.py` (Subscription, SubscriptionItem, SubscriptionEvent)
- Create: `backend/app/schemas/subscription.py`
- Create: `backend/app/services/subscription_lifecycle.py`
- Create: `backend/app/api/v1/subscriptions.py`
- Test: `backend/tests/test_subscription_lifecycle.py`

**Interfaces:**
- State transitions:
  - `Draft -> Quotation` (Generates Quote)
  - `Quotation -> Draft` (Revise quote into new version)
  - `Quotation -> Confirmed` (Record acceptance)
  - `Confirmed -> Active` (Activate with billing anchor)
  - `Active -> Closed` (Terminal state with closure reason)
  - `Draft/Quotation/Confirmed -> Closed` (Abandon/cancel)
- Disallowed transitions return `409 INVALID_STATE_TRANSITION`.

- [ ] **Step 1: Write test matrix for all legal and illegal state transitions, verifying optimistic locking via `version`.**
- [ ] **Step 2: Implement `SubscriptionLifecycleService` with transition methods, transactional events, and audit logging.**
- [ ] **Step 3: Implement subscription REST endpoints.**
- [ ] **Step 4: Verify all transition tests pass.**

#### Task 3.2: Quotation Snapshot & PDF Generation
**Files:**
- Create: `backend/app/models/quote.py` (Quote, QuoteItem)
- Create: `backend/app/services/quote_service.py`
- Create: `backend/app/templates/quote.html`
- Create: `backend/app/integrations/pdf_renderer.py` (WeasyPrint)
- Create: `backend/app/integrations/storage.py` (MinIO/S3 client)
- Create: `backend/app/api/v1/quotes.py`
- Test: `backend/tests/test_quotes.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/subscriptions/{id}/quote` (Issues immutable quote snapshot, 30 days validity)
  - `POST /api/v1/quotes/{id}/accept` (Validates expiry; records acceptance actor, time, source)
  - `GET /api/v1/quotes/{id}/pdf` (Returns signed stream or file)

- [ ] **Step 1: Write test for quote expiration (cannot accept quote after 30 days).**
- [ ] **Step 2: Write test verifying quote item snapshot is immutable even if plan price changes afterwards.**
- [ ] **Step 3: Implement HTML template and WeasyPrint PDF renderer.**
- [ ] **Step 4: Implement S3 object storage upload and signed download URL.**
- [ ] **Step 5: Verify test passes.**

---

### Phase 4: Financial Calculation Engine, Tax Rules & Discounts

#### Task 4.1: Deterministic Line Calculation & Tax Rules
**Files:**
- Create: `backend/app/models/tax.py` (TaxRule)
- Create: `backend/app/services/financial_math.py`
- Test: `backend/tests/test_financial_math.py`

**Interfaces:**
- Produces: `FinancialMathService.calculate_line_items(...)`
  - Formula: `Unit Price * Quantity -> - Eligible Discount -> Taxable Base -> + Applicable Taxes -> Line Total`
  - Rounding: Half-up to currency minor unit at line-tax level, then sum.
  - Verification: 2 seats * ₹1,000 = ₹2,000 subtotal, 10% discount (-₹200) = ₹1,800 taxable base, 18% tax (+₹324) = **₹2,124.00**.

- [ ] **Step 1: Write unit tests covering both tax-exclusive and tax-inclusive calculations, zero discount, multiple lines, and precision bounds.**
- [ ] **Step 2: Implement `financial_math.py` using `decimal.Decimal` and `ROUND_HALF_UP`.**
- [ ] **Step 3: Implement `TaxRule` repository with jurisdiction and category matching.**
- [ ] **Step 4: Verify arithmetic test passes with exact penny precision.**

#### Task 4.2: Discount & Campaign Engine
**Files:**
- Create: `backend/app/models/discount.py` (Discount, DiscountRedemption)
- Create: `backend/app/schemas/discount.py`
- Create: `backend/app/services/discount_service.py`
- Create: `backend/app/api/v1/discounts.py`
- Test: `backend/tests/test_discounts.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/discounts`
  - `POST /api/v1/discounts/validate` (Preview without consuming quota)
  - `DiscountService.redeem_discount_transactional(...)` (Consumes count with `SELECT FOR UPDATE`)

- [ ] **Step 1: Write test for discount eligibility (date window, minimum spend, customer limit, global limit).**
- [ ] **Step 2: Write test for concurrent redemption on final quota (only 1 succeeds, other rejects).**
- [ ] **Step 3: Implement discount service and redemption tracker.**
- [ ] **Step 4: Verify test passes.**

---

### Phase 5: Automated Billing Engine & Invoice Invariants

#### Task 5.1: Invoice Data Model & Manual Issuance
**Files:**
- Create: `backend/app/models/invoice.py` (Invoice, InvoiceLine, InvoiceTaxLine, BillingSchedule)
- Create: `backend/app/schemas/invoice.py`
- Create: `backend/app/services/invoice_service.py`
- Create: `backend/app/api/v1/invoices.py`
- Test: `backend/tests/test_invoices.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/invoices` (Filters: customer, date, status, overdue)
  - `GET /api/v1/invoices/{id}`
  - Statuses: `DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `VOID`
  - Overdue: Derived boolean `(balance > 0 and tenant_local_date > due_date)`.
  - Immutable issue snapshot: Unit prices, tax rates, applied discounts recorded permanently.

- [ ] **Step 1: Write test verifying that once an invoice is ISSUED, editing line prices directly is rejected.**
- [ ] **Step 2: Implement invoice model with unique constraint `(tenant_id, invoice_number)`.**
- [ ] **Step 3: Implement Jinja2 HTML invoice template and WeasyPrint PDF renderer.**
- [ ] **Step 4: Verify test passes.**

#### Task 5.2: Celery Recurring Billing Worker
**Files:**
- Create: `backend/app/workers/celery_app.py`
- Create: `backend/app/workers/tasks/billing_tasks.py`
- Create: `backend/app/services/billing_schedule_service.py`
- Test: `backend/tests/test_billing_worker.py`

**Interfaces:**
- Produces:
  - `generate_due_invoices_task()` scheduled every 15 minutes by Celery Beat.
  - Idempotency guarantee: Unique constraint on `(tenant_id, subscription_id, period_start, period_end, invoice_kind)`.
  - Anchor clamping: Day 29/30/31 clamped to month end (e.g. Feb 28/29, Mar 31).

- [ ] **Step 1: Write test simulating running the billing task twice for the same billing cycle; verify exactly one invoice is generated.**
- [ ] **Step 2: Write test for month-end clamp logic for Jan 31 -> Feb 28 -> Mar 31.**
- [ ] **Step 3: Implement Celery billing worker with `SKIP LOCKED` schedule query and transactional execution.**
- [ ] **Step 4: Verify test passes.**

---

### Phase 6: Payment Ledger, Allocations & Credit Notes

#### Task 6.1: Payment Recording & Multi-Invoice Allocation
**Files:**
- Create: `backend/app/models/payment.py` (Payment, PaymentAllocation, Refund)
- Create: `backend/app/schemas/payment.py`
- Create: `backend/app/services/payment_service.py`
- Create: `backend/app/api/v1/payments.py`
- Test: `backend/tests/test_payments.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/payments` (Records payment amount, method, external reference)
  - `POST /api/v1/payments/{id}/allocations` (Allocates across customer's invoices; updates `paid_total` and `balance_due`)
  - `POST /api/v1/payments/{id}/reverse` (Compensating reversal transaction; reopens invoice balances)

- [ ] **Step 1: Write test for partial payment (₹1,000 against ₹2,124 -> balance ₹1,124, `PARTIALLY_PAID`).**
- [ ] **Step 2: Write test for multi-invoice allocation (₹3,000 allocated across ₹2,000 invoice and ₹1,000 invoice).**
- [ ] **Step 3: Write test rejecting cross-customer or cross-currency allocation.**
- [ ] **Step 4: Write test verifying payment reversal restores balance without deleting the payment record.**
- [ ] **Step 5: Implement `PaymentService` with transactional row locking on payments and invoices.**
- [ ] **Step 6: Verify all payment tests pass.**

#### Task 6.2: Credit Notes & Financial Corrections
**Files:**
- Create: `backend/app/models/credit_note.py` (CreditNote, CreditNoteLine)
- Create: `backend/app/services/credit_note_service.py`
- Create: `backend/app/api/v1/credit_notes.py`
- Test: `backend/tests/test_credit_notes.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/invoices/{id}/credit-notes` (Issues numbered credit note reducing invoice balance)

- [ ] **Step 1: Write test ensuring credit note cannot exceed remaining invoice payable balance.**
- [ ] **Step 2: Implement CreditNote service and sequence generation.**
- [ ] **Step 3: Verify test passes.**

---

### Phase 7: Analytics Engine, Receivables Aging & CSV Exports

#### Task 7.1: Real-time Analytics & Metric Calculation
**Files:**
- Create: `backend/app/services/analytics_service.py`
- Create: `backend/app/api/v1/analytics.py`
- Test: `backend/tests/test_analytics.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/analytics/summary` (Active Subscriptions count, MRR, ARR, Invoiced Revenue, Cash Collected, Outstanding Receivables, Overdue Amount)
  - `GET /api/v1/analytics/revenue-trend` (12-month MRR and cash collection trend)
  - `GET /api/v1/analytics/aging` (Buckets: Current, 1–30, 31–60, 61–90, 90+ days past due)
  - `GET /api/v1/analytics/subscriptions` (Status breakdown and churn metrics)
  - Redis caching with tenant-scoped cache keys and event-driven invalidation.

- [ ] **Step 1: Write test asserting MRR formula: `sum(normalized monthly contracted net amount)` for active subscriptions only.**
- [ ] **Step 2: Write test verifying aging bucket sums reconcile with open invoice balances.**
- [ ] **Step 3: Implement SQL aggregate queries with proper tenant boundaries and currency grouping.**
- [ ] **Step 4: Verify test passes.**

#### Task 7.2: Asynchronous CSV Reports & Export Worker
**Files:**
- Create: `backend/app/workers/tasks/report_tasks.py`
- Create: `backend/app/api/v1/reports.py`
- Test: `backend/tests/test_reports.py`

**Interfaces:**
- Produces: `POST /api/v1/reports/export` (Exports customers, subscriptions, invoices, or payments to CSV via Celery, stores in MinIO, returns signed URL).

- [ ] **Step 1: Write test verifying export includes all required columns and sanitizes CSV injection characters (`=`, `+`, `-`, `@`).**
- [ ] **Step 2: Implement CSV streaming and S3 storage.**
- [ ] **Step 3: Verify test passes.**

---

### Phase 8: Transactional Email Outbox & Background Monitoring

#### Task 8.1: Transactional Outbox Pattern & Mailer
**Files:**
- Create: `backend/app/models/outbox.py` (OutboxEvent, NotificationDelivery)
- Create: `backend/app/services/outbox_service.py`
- Create: `backend/app/workers/tasks/notification_tasks.py`
- Create: `backend/app/integrations/email_sender.py`
- Test: `backend/tests/test_notifications.py`

**Interfaces:**
- Produces:
  - Events: `QUOTE_ISSUED`, `SUBSCRIPTION_ACTIVATED`, `INVOICE_ISSUED`, `PAYMENT_RECORDED`, `INVOICE_OVERDUE`.
  - Deduping constraint: `(event_id, template_id, recipient)` delivery record.
  - Mailpit delivery in local development.

- [ ] **Step 1: Write test verifying outbox events are committed in the same DB transaction as domain actions.**
- [ ] **Step 2: Write test verifying worker crash retry does not send duplicate emails.**
- [ ] **Step 3: Implement Jinja2 HTML email templates and SMTP dispatcher.**
- [ ] **Step 4: Verify test passes.**

#### Task 8.2: Audit Logs & Job Monitoring API
**Files:**
- Create: `backend/app/api/v1/audit.py`
- Create: `backend/app/api/v1/jobs.py`
- Test: `backend/tests/test_audit.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/audit-logs` (Filtered by actor, entity, date range)
  - `GET /api/v1/jobs` (Celery task queue status, failure details, retry action)

- [ ] **Step 1: Write test verifying audit logs capture actor, tenant, timestamp, and diff payload.**
- [ ] **Step 2: Implement audit querying and safe retry endpoint for failed background jobs.**
- [ ] **Step 3: Verify test passes.**

---

### Phase 9: Google Gemini AI Advisory Gateway

#### Task 9.1: Gemini AI Integration & Safety Boundaries
**Files:**
- Create: `backend/app/integrations/gemini_client.py`
- Create: `backend/app/services/ai_service.py`
- Create: `backend/app/schemas/ai.py`
- Create: `backend/app/api/v1/ai.py`
- Test: `backend/tests/test_ai_service.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/ai/insights`:
    - `EXPLAIN_DASHBOARD`: Natural-language explanation of pre-computed metrics.
    - `SUBSCRIPTION_TRENDS`: Summarizes status & overdue patterns.
    - `BILLING_ASSISTANT`: Answers domain lifecycle and pricing questions using baked-in PRD documentation.
    - `NATURAL_LANGUAGE_FILTER`: Converts user text into strict Pydantic filter schema (never raw SQL).
  - Rate limiting: Max requests per user per day.
  - Fallback: Gracefully returns advisory error when `AI_ENABLED=false` or quota 429 occurs; core billing operates uninterrupted.

- [ ] **Step 1: Write test verifying that when Gemini is unreachable or returns 429, API returns structured fallback without failing.**
- [ ] **Step 2: Write test verifying Pydantic schema validation for NL-to-filter output, rejecting any unstructured SQL injection.**
- [ ] **Step 3: Implement `google-genai` client integration with system instructions and Pydantic structured output.**
- [ ] **Step 4: Verify test passes.**

---

### Phase 10: Frontend SPA Implementation (React 19 + TypeScript + Vite)

#### Task 10.1: Shell, Navigation, Auth State & Router
**Files:**
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/app/providers.tsx`
- Create: `frontend/src/lib/axios.ts`
- Create: `frontend/src/features/auth/AuthContext.tsx`
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Navbar.tsx`

**Interfaces:**
- Produces: Protected route hierarchy, sidebar with role-aware navigation, user avatar, tenant switcher, and global breadcrumbs.

- [ ] **Step 1: Implement Axios interceptor for CSRF tokens and 401 unauthenticated redirects.**
- [ ] **Step 2: Implement React Router route guards checking membership and RBAC permissions.**
- [ ] **Step 3: Implement responsive layout (desktop sidebar, mobile drawer).**

#### Task 10.2: Dashboard & Analytics Charts
**Files:**
- Create: `frontend/src/features/dashboard/DashboardPage.tsx`
- Create: `frontend/src/features/dashboard/components/KpiCard.tsx`
- Create: `frontend/src/features/dashboard/components/RevenueChart.tsx`
- Create: `frontend/src/features/dashboard/components/AgingChart.tsx`
- Create: `frontend/src/features/ai/AiInsightWidget.tsx`

**Interfaces:**
- Produces: Visual KPI cards (Active Subscriptions, MRR, Invoiced Revenue, Overdue), 12-month trend charts via Recharts, aging bucket visualizations, and optional AI summary drawer.

- [ ] **Step 1: Implement KPI summary cards with trend indicators.**
- [ ] **Step 2: Implement Recharts area and bar charts with drill-down click handlers.**
- [ ] **Step 3: Integrate AI explanation drawer with disclaimer labels.**

#### Task 10.3: Customers, Plans & Subscription Management Pages
**Files:**
- Create: `frontend/src/features/customers/CustomerListPage.tsx`
- Create: `frontend/src/features/customers/CustomerDetailPage.tsx`
- Create: `frontend/src/features/plans/PlanListPage.tsx`
- Create: `frontend/src/features/subscriptions/SubscriptionListPage.tsx`
- Create: `frontend/src/features/subscriptions/SubscriptionDetailPage.tsx`
- Create: `frontend/src/features/subscriptions/SubscriptionWizard.tsx`
- Create: `frontend/src/features/quotes/QuoteDetailPage.tsx`

**Interfaces:**
- Produces:
  - Customer CRUD, plan version management.
  - Subscription creation wizard (Customer -> Plan -> Qty -> Dates -> Currency -> Discount preview).
  - Subscription Detail with status timeline (`Draft -> Quotation -> Confirmed -> Active -> Closed`), contextual action buttons (Issue Quote, Accept, Activate, Close), and state history.
  - Quote viewer with embedded PDF preview and Accept/Reject buttons.

- [ ] **Step 1: Implement TanStack Table with server pagination, sorting, and search for Customer and Subscription lists.**
- [ ] **Step 2: Implement React Hook Form + Zod validation for subscription creation wizard.**
- [ ] **Step 3: Implement subscription detail view with state badge, allowed action dialogs, and event audit history.**

#### Task 10.4: Invoices, Discounts & Payment Allocation Pages
**Files:**
- Create: `frontend/src/features/invoices/InvoiceListPage.tsx`
- Create: `frontend/src/features/invoices/InvoiceDetailPage.tsx`
- Create: `frontend/src/features/discounts/DiscountListPage.tsx`
- Create: `frontend/src/features/payments/PaymentListPage.tsx`
- Create: `frontend/src/features/payments/PaymentNewPage.tsx`

**Interfaces:**
- Produces:
  - Invoice detail with line breakdowns, tax tables, payment history, and PDF download button.
  - Payment entry form with dynamic invoice allocation rows showing remaining balances in real-time.
  - Discount campaign manager with usage meters.

- [ ] **Step 1: Implement Invoice list with overdue highlighting and status filters.**
- [ ] **Step 2: Implement Payment creation page with multi-invoice allocation table and real-time balance calculations.**
- [ ] **Step 3: Implement Discount code management page.**

#### Task 10.5: Operations, Settings & Audit Log Pages
**Files:**
- Create: `frontend/src/features/settings/SettingsPage.tsx`
- Create: `frontend/src/features/settings/TeamPage.tsx`
- Create: `frontend/src/features/audit/AuditLogPage.tsx`
- Create: `frontend/src/features/jobs/JobsMonitorPage.tsx`

**Interfaces:**
- Produces: Organization settings, team invitation & role selector, audit event explorer, and background job queue monitor with retry buttons.

- [ ] **Step 1: Implement organization settings form (timezone, currency, numbering format).**
- [ ] **Step 2: Implement team membership management with role assignment.**
- [ ] **Step 3: Implement audit log and Celery job queue monitoring views.**

---

### Phase 11: End-to-End Verification, Seed Dataset & Performance Benchmark

#### Task 11.1: E2E Acceptance Test Suite
**Files:**
- Create: `tests/e2e/test_full_journey.py` (API level)
- Create: `frontend/e2e/journey.spec.ts` (Playwright browser level)

**Interfaces:**
- Validates:
  - **Journey A:** Create customer & plan -> Draft (2 seats * ₹1,000) -> Issue Quote -> Accept -> Confirm -> Activate -> Bill (₹2,124 with 18% tax) -> Record ₹1,000 partial payment -> Record ₹1,124 final payment -> Invoice Paid.
  - **Journey B:** Discount `WELCOME10` applied -> Single redemption consumed -> Second usage rejected.
  - **Journey C:** Overdue detection when due date passes with balance > 0 -> Appears in aging bucket.

- [ ] **Step 1: Write and run full API journey test exercising all 18 acceptance criteria from PRD Section 17.**
- [ ] **Step 2: Write and run Playwright browser test covering login, subscription wizard, and quote acceptance.**
- [ ] **Step 3: Verify all E2E tests pass cleanly.**

#### Task 11.2: Deterministic Seeding & Locust Load Test (<2s SLO)
**Files:**
- Create: `backend/app/scripts/seed_load_data.py`
- Create: `backend/tests/locustfile.py`

**Interfaces:**
- Deliverables:
  - Seed script generating: 3 tenants, 10 users, 300 customers, 20 plans, **10,000 subscriptions**, **100,000 invoices**, and **200,000 payment allocations**.
  - Locust load script simulating 100 concurrent users browsing dashboard, customer lists, invoice details, and running searches.
  - Target: **p95 API response time < 2.0s** under the seeded dataset.

- [ ] **Step 1: Implement high-performance bulk insert seed script using SQLAlchemy `insert().values()`.**
- [ ] **Step 2: Run seed script against PostgreSQL staging database.**
- [ ] **Step 3: Execute Locust benchmark with 100 concurrent workers for 5 minutes.**
- [ ] **Step 4: Verify p95 latency is under 2.0s across all standard endpoints.**

---

## Deliverables & Acceptance Checklist

1. [ ] Fully functional Monorepo: `frontend` (React 19 + TS), `backend` (FastAPI + SQLAlchemy), `worker` (Celery).
2. [ ] Complete database migrations with Alembic and PostgreSQL ACID isolation.
3. [ ] Server-enforced state machine (`Draft -> Quotation -> Confirmed -> Active -> Closed`).
4. [ ] Immutable quotation and invoice snapshots with WeasyPrint PDF generation.
5. [ ] Configurable tax rules and transactional discount redemption locking.
6. [ ] Celery-driven recurring billing worker with duplicate-period prevention.
7. [ ] Manual payment recording, multi-invoice allocation, and compensating reversals.
8. [ ] Real-time financial dashboard (MRR, ARR, Aging buckets, Cash collections) with CSV exports.
9. [ ] Advisory Gemini AI integration with fallback and strict Pydantic output validation.
10. [ ] 10k-subscription deterministic seed script and verified <2s p95 API load test.
