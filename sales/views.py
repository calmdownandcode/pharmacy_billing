from django.shortcuts import render, redirect, get_object_or_404
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
        customer = get_object_or_404(Customer, id=customer_id)
        invoice = Invoice.objects.create(
            customer=customer,
            invoice_date=date.today()
        )
        return redirect('invoice_detail', invoice_id=invoice.id)

    return render(
        request,
        'sales/invoice_create.html',
        {'customers': customers}
    )

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == "POST":
        product_id = request.POST.get("product")
        batch_id = request.POST.get("batch")
        qty = int(request.POST.get("qty") or 0)
        free_qty = int(request.POST.get("free_qty") or 0)
        rate = request.POST.get("rate")

        product = get_object_or_404(Product, id=product_id)
        batch = get_object_or_404(Batch, id=batch_id)

        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            batch=batch,
            qty=qty,
            free_qty=free_qty,
            rate=rate
        )
        return redirect('invoice_detail', invoice_id=invoice.id)

    products = Product.objects.all()
    batches = Batch.objects.filter(stock_qty__gt=0)  # Only show available stock batches
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
    invoice = get_object_or_404(Invoice, id=invoice_id)
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

def create_sales_return(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == "POST":
        sales_return = SalesReturn.objects.create(
            invoice=invoice,
            return_date=date.today()
        )
        item_id = request.POST.get("invoice_item")
        qty = int(request.POST.get("qty") or 0)

        invoice_item = get_object_or_404(InvoiceItem, id=item_id)

        SalesReturnItem.objects.create(
            sales_return=sales_return,
            invoice_item=invoice_item,
            qty=qty
        )
        return redirect('invoice_detail', invoice_id=invoice.id)

    items = invoice.items.all()
    return render(
        request,
        'sales/create_sales_return.html',
        {
            'invoice': invoice,
            'items': items
        }
    )
