import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import TenantUserContext, get_current_tenant_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceListResponse, InvoiceResponse
from app.services.sequence_service import SequenceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: str | None = Query(None, alias="status"),
    customer_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List invoices with pagination and status filters."""
    tenant_id = ctx.session.tenant_id
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.customer))
        .where(Invoice.tenant_id == tenant_id)
    )

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter.upper())
    if customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(Invoice.issue_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    results = (await db.execute(stmt)).scalars().all()

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create manual invoice for a customer."""
    tenant_id = ctx.session.tenant_id

    customer = await db.get(Customer, payload.customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    try:
        inv_number = await SequenceService.get_next_number(db, tenant_id, "invoice")
    except Exception:
        count = (
            await db.execute(
                select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
            )
        ).scalar_one()
        inv_number = f"INV-2026-27-{count + 1:04d}"

    tax_amount = (payload.subtotal * payload.tax_rate) / Decimal("100.00")
    total_amount = payload.subtotal + tax_amount

    inv = Invoice(
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        subscription_id=payload.subscription_id,
        invoice_number=inv_number,
        status="ISSUED",
        issue_date=datetime.now(UTC),
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        tax_rate=payload.tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        amount_paid=Decimal("0.00"),
        balance_due=total_amount,
        currency=customer.currency_preference or "INR",
        notes=payload.notes,
    )
    db.add(inv)
    customer.outstanding_balance += total_amount
    await db.commit()
    await db.refresh(inv)

    stmt = select(Invoice).options(selectinload(Invoice.customer)).where(Invoice.id == inv.id)
    return (await db.execute(stmt)).scalar_one()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get invoice by ID."""
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.customer))
        .where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == ctx.session.tenant_id,
        )
    )
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return inv


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
async def get_invoice_html(
    invoice_id: uuid.UUID,
    ctx: TenantUserContext = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Render a printable HTML tax invoice compliant with Indian GST requirements."""
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.customer))
        .where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == ctx.session.tenant_id,
        )
    )
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    tenant_name = ctx.tenant.name if ctx.tenant else "Acme Cloud Technologies Pvt Ltd"
    cust_name = inv.customer.name if inv.customer else "Valued Client"
    cust_gst = inv.customer.tax_id or "URP (Unregistered Person)"
    cust_addr = f"{inv.customer.billing_address_line1 or ''}, {inv.customer.billing_city or ''} {inv.customer.billing_postal_code or ''}"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Tax Invoice {inv.invoice_number}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #1e293b; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #1e3a8a; }}
        .invoice-title {{ font-size: 20px; text-align: right; color: #475569; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; margin-top: 24px; gap: 20px; }}
        .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
        .box h3 {{ margin-top: 0; font-size: 14px; text-transform: uppercase; color: #64748b; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
        th {{ background: #f1f5f9; text-align: left; padding: 10px; border-bottom: 2px solid #cbd5e1; }}
        td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
        .text-right {{ text-align: right; }}
        .totals {{ margin-top: 20px; float: right; width: 300px; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge-PAID {{ background: #dcfce7; color: #15803d; }}
        .badge-ISSUED {{ background: #dbeafe; color: #1d4ed8; }}
        .badge-OVERDUE {{ background: #fee2e2; color: #b91c1c; }}
        .footer {{ margin-top: 100px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo">{tenant_name}</div>
            <p style="color: #64748b; margin: 4px 0;">SaaS Subscription Management Platform</p>
        </div>
        <div class="invoice-title">
            <span class="badge badge-{inv.status}">{inv.status}</span>
            <h2 style="margin: 8px 0 0 0; color: #0f172a;">{inv.invoice_number}</h2>
        </div>
    </div>

    <div class="meta-grid">
        <div class="box">
            <h3>Billed To</h3>
            <strong>{cust_name}</strong><br>
            {cust_addr}<br>
            <strong>GSTIN:</strong> {cust_gst}<br>
            <strong>Currency:</strong> {inv.currency}
        </div>
        <div class="box">
            <h3>Invoice Details</h3>
            <strong>Issue Date:</strong> {inv.issue_date.strftime('%d-%b-%Y')}<br>
            <strong>Due Date:</strong> {inv.due_date.strftime('%d-%b-%Y')}<br>
            <strong>Place of Supply:</strong> Karnataka (29)<br>
            <strong>Reverse Charge:</strong> No
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th>SAC / HSN</th>
                <th class="text-right">Taxable Value</th>
                <th class="text-right">GST ({inv.tax_rate}%)</th>
                <th class="text-right">Total Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>B2B SaaS Cloud Services & Platform Subscription</td>
                <td>998313</td>
                <td class="text-right">{inv.currency} {inv.subtotal:,.2f}</td>
                <td class="text-right">{inv.currency} {inv.tax_amount:,.2f}</td>
                <td class="text-right"><strong>{inv.currency} {inv.total_amount:,.2f}</strong></td>
            </tr>
        </tbody>
    </table>

    <div class="totals">
        <table style="margin-top: 0;">
            <tr>
                <td><strong>Subtotal:</strong></td>
                <td class="text-right">{inv.currency} {inv.subtotal:,.2f}</td>
            </tr>
            <tr>
                <td><strong>IGST / GST ({inv.tax_rate}%):</strong></td>
                <td class="text-right">{inv.currency} {inv.tax_amount:,.2f}</td>
            </tr>
            <tr style="border-top: 2px solid #0f172a;">
                <td><h3>Grand Total:</h3></td>
                <td class="text-right"><h3>{inv.currency} {inv.total_amount:,.2f}</h3></td>
            </tr>
            <tr>
                <td>Amount Paid:</td>
                <td class="text-right">{inv.currency} {inv.amount_paid:,.2f}</td>
            </tr>
            <tr style="color: #b91c1c;">
                <td><strong>Balance Due:</strong></td>
                <td class="text-right"><strong>{inv.currency} {inv.balance_due:,.2f}</strong></td>
            </tr>
        </table>
    </div>

    <div style="clear: both;"></div>

    <div class="footer">
        This is a computer-generated invoice and does not require a physical signature. Powered by Multi-Tenant B2B Subscription Engine.
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)
