from django.contrib import admin
from .models import (Company, Customer, Product, Batch, Invoice, InvoiceItem, Payment,Supplier,
    PurchaseInvoice,PurchaseItem  )

admin.site.register(Company)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Batch)
admin.site.register(Payment)
admin.site.register(Supplier)
admin.site.register(PurchaseInvoice)
admin.site.register(PurchaseItem)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]


