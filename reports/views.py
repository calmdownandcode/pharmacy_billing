from datetime import date, timedelta
from django.shortcuts import render
from core.models import Batch, Customer


def stock_report(request):

    batches = Batch.objects.select_related(
        'product'
    ).all().order_by(
        'product__name'
    )

    return render(
        request,
        'reports/stock_report.html',
        {
            'batches': batches
        }
    )

def outstanding_report(request):

    data = []

    customers = Customer.objects.all()

    for customer in customers:

        invoice_total = sum(
            invoice.net_amount
            for invoice in customer.invoice_set.all()
        )

        payment_total = sum(
            payment.amount
            for payment in customer.payments.all()
        )

        outstanding = (
            invoice_total -
            payment_total
        )

        if outstanding > 0:
            data.append({
                "customer": customer,
                "outstanding": outstanding
            })

    data.sort(
        key=lambda x: x["outstanding"],
        reverse=True
    )

    return render(
        request,
        "reports/outstanding_report.html",
        {
            "data": data
        }
    )

def expiry_report(request):

    today = date.today()

    expiry_limit = (
        today +
        timedelta(days=90)
    )

    batches = Batch.objects.filter(
        expiry_date__lte=expiry_limit,
        stock_qty__gt=0
    ).order_by(
        'expiry_date'
    )

    return render(
        request,
        'reports/expiry_report.html',
        {
            'batches': batches
        }
    )

def low_stock_report(request):

    batches = Batch.objects.filter(
        stock_qty__lt=20,
        stock_qty__gt=0
    ).order_by(
        'stock_qty'
    )

    return render(
        request,
        'reports/low_stock_report.html',
        {
            'batches': batches
        }
    )