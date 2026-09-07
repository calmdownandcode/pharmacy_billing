from django.shortcuts import render
from datetime import date, timedelta

from core.models import (
    Batch,
    Customer,
    Invoice,
    PurchaseInvoice
)

def dashboard_home(request):

    today = date.today()

    today_sales = sum(
        invoice.net_amount
        for invoice in Invoice.objects.filter(
            invoice_date=today
        )
    )

    today_purchases = PurchaseInvoice.objects.filter(
        invoice_date=today
    ).count()

    low_stock_count = Batch.objects.filter(
        stock_qty__lt=20,
        stock_qty__gt=0
    ).count()

    expiry_limit = today + timedelta(days=90)

    expiring_count = Batch.objects.filter(
        expiry_date__lte=expiry_limit,
        stock_qty__gt=0
    ).count()

    return render(
        request,
        'dashboard/dashboard.html',
        {
            'today_sales': today_sales,
            'today_purchases': today_purchases,
            'low_stock_count': low_stock_count,
            'expiring_count': expiring_count,
        }
    )


