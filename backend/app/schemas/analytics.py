from decimal import Decimal
from pydantic import BaseModel


class MonthlyTrend(BaseModel):
    month: str
    mrr: Decimal
    invoiced: Decimal
    collected: Decimal


class DashboardSummaryResponse(BaseModel):
    mrr: Decimal
    arr: Decimal
    active_subscriptions: int
    total_customers: int
    overdue_invoices_amount: Decimal
    overdue_invoices_count: int
    total_collected_amount: Decimal
    currency: str
    monthly_trends: list[MonthlyTrend]
