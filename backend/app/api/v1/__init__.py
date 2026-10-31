from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.payments import router as payments_router
from app.api.v1.plans import router as plans_router
from app.api.v1.settings import router as settings_router
from app.api.v1.subscriptions import router as subscriptions_router

__all__ = [
    "analytics_router",
    "auth_router",
    "customers_router",
    "invoices_router",
    "payments_router",
    "plans_router",
    "settings_router",
    "subscriptions_router",
]
