from django.shortcuts import render, redirect
from core.models import (
    Supplier,
    PurchaseInvoice,
    PurchaseItem,
    Product
)


def purchase_create(request):

    suppliers = Supplier.objects.all()

    if request.method == "POST":

        supplier = Supplier.objects.get(
            id=request.POST.get("supplier")
        )

        purchase = PurchaseInvoice.objects.create(
            supplier=supplier,
            invoice_no=request.POST.get("invoice_no"),
            invoice_date=request.POST.get("invoice_date")
        )

        return redirect(
            'purchase_detail',
             purchase_id=purchase.id
        )

    return render(
        request,
        'purchases/purchase_create.html',
        {
            'suppliers': suppliers
        }
    )

def purchase_detail(request, purchase_id):

    purchase = PurchaseInvoice.objects.get(
        id=purchase_id
    )

    if request.method == "POST":

        product = Product.objects.get(
            id=request.POST.get("product")
        )

        PurchaseItem.objects.create(
            purchase_invoice=purchase,
            product=product,
            batch_no=request.POST.get("batch_no"),
            expiry_date=request.POST.get("expiry_date"),
            qty=request.POST.get("qty"),
            mrp=request.POST.get("mrp"),
            ptr=request.POST.get("ptr"),
            pts=request.POST.get("pts")
        )

        return redirect(
            'purchase_detail',
            purchase_id=purchase.id
        )

    products = Product.objects.all()

    items = purchase.items.all()

    return render(
        request,
        'purchases/purchase_detail.html',
        {
            'purchase': purchase,
            'products': products,
            'items': items
        }
    )