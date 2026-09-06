from django.contrib import admin
from .models import (Company, Customer, Product, Batch, Invoice, InvoiceItem)

admin.site.register(Company)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Batch)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
