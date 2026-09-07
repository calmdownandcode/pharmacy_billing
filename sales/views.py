from django.shortcuts import render, redirect
from core.models import (
    Customer,
    Invoice,
    Product,
    Batch,
    InvoiceItem,
    Company,
    SalesReturn,
    SalesReturnItem,
)
from datetime import date


def invoice_create(request):

    customers = Customer.objects.all()

    if request.method == "POST":

        customer_id = request.POST.get("customer")

        customer = Customer.objects.get(id=customer_id)

        invoice = Invoice.objects.create(
            customer=customer,
            invoice_date=date.today()
        )

        return redirect(
            'invoice_detail',
            invoice_id=invoice.id
        )

    return render(
        request,
        'sales/invoice_create.html',
        {
            'customers': customers
        }
    )

def invoice_detail(request, invoice_id):

    invoice = Invoice.objects.get(id=invoice_id)

    batch = Batch.objects.get(id=batch_id)

    InvoiceItem.objects.create(
        invoice=invoice,
        product=batch.product,
        batch=batch,
        qty=qty,
        free_qty=free_qty,
        rate=batch.pts
    )

    if request.method == "POST":

        product_id = request.POST.get("product")
        batch_id = request.POST.get("batch")

        qty = int(request.POST.get("qty"))
        free_qty = int(request.POST.get("free_qty"))

        rate = request.POST.get("rate")

        product = Product.objects.get(id=product_id)
        batch = Batch.objects.get(id=batch_id)

        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            batch=batch,
            qty=qty,
            free_qty=free_qty,
            rate=rate
        )

        return redirect(
            'invoice_detail',
            invoice_id=invoice.id
        )

    products = Product.objects.all()
    batches = Batch.objects.all()

    items = invoice.items.all()

    return render(
        request,
        'sales/invoice_detail.html',
        {
            'invoice': invoice,
            'products': products,
            'items': items,
            'batches': batches,
        }
    )

def print_invoice(request, invoice_id):

    invoice = Invoice.objects.get(id=invoice_id)

    items = invoice.items.all()

    company = Company.objects.first()

    return render(
        request,
        'sales/print_invoice.html',
        {
            'invoice': invoice,
            'items': items,
            'company': company
        }
    )

def create_sales_return(
    request,
    invoice_id
):

    invoice = Invoice.objects.get(
        id=invoice_id
    )

    if request.method == "POST":

        sales_return = SalesReturn.objects.create(
            invoice=invoice,
            return_date=date.today()
        )

        item_id = request.POST.get(
            "invoice_item"
        )

        qty = int(
            request.POST.get("qty")
        )

        invoice_item = InvoiceItem.objects.get(
            id=item_id
        )

        SalesReturnItem.objects.create(
            sales_return=sales_return,
            invoice_item=invoice_item,
            qty=qty
        )

        return redirect(
            'invoice_detail',
            invoice_id=invoice.id
        )

    items = invoice.items.all()

    return render(
        request,
        'sales/create_sales_return.html',
        {
            'invoice': invoice,
            'items': items
        }
    )