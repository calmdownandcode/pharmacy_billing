from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.db.models import CheckConstraint



class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    state = models.CharField(max_length=100, default="BIHAR")
    city = models.TextField(default = 'X')
    phone = models.CharField(max_length=20)
    gst_no = models.CharField(max_length=20)
    drug_license_no = models.CharField(max_length=50)


    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    state = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    gst_no = models.CharField(max_length=20, blank=True)
    drug_license_no = models.CharField(max_length=50, blank=True)
    

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    pack = models.CharField(max_length=50)
    hsn_code = models.CharField(max_length=20)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class Batch(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="batches"
    )

    batch_no = models.CharField(max_length=50)

    expiry_date = models.DateField()

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    ptr = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    pts = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock_qty = models.IntegerField(default=0)

    class Meta:
            unique_together = (
                'product',
                'batch_no'
            )

            constraints = [
                CheckConstraint(
                    condition=Q(stock_qty__gte=0),
                    name="stock_not_negative"
                )
            ]

    def __str__(self):
        return f"{self.product.name} - {self.batch_no}"


class Invoice(models.Model):
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank = True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT
    )

    invoice_date = models.DateField(auto_now_add=True)

    due_date = models.DateField(
        null=True,
        blank=True
    )

    order_no = models.CharField(
        max_length=50,
        blank=True
    )

    taxable_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    cgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    sgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    igst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    round_off = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.invoice_number

    def calculate_totals(self):
        items = self.items.all()
        taxable = Decimal("0.00")
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")
        igst = Decimal("0.00")

        for item in items:
            taxable += Decimal(str(item.taxable_value or 0))
            cgst += Decimal(str(item.cgst_amount or 0))
            sgst += Decimal(str(item.sgst_amount or 0))
            igst += Decimal(str(item.igst_amount or 0))

        self.taxable_amount = taxable
        self.cgst_amount = cgst
        self.sgst_amount = sgst
        self.igst_amount = igst
        self.net_amount = taxable + cgst + sgst + igst
        self.save(update_fields=['taxable_amount', 'cgst_amount', 'sgst_amount', 'igst_amount', 'net_amount'])

    def save(self, *args, **kwargs):

        if not self.invoice_number:

            last_invoice = Invoice.objects.order_by('-id').first()

            if last_invoice:
                next_number = last_invoice.id + 1
            else:
                next_number = 1

            self.invoice_number = f"INV-{next_number:05d}"

        super().save(*args, **kwargs)



class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT
    )

    qty = models.IntegerField()

    free_qty = models.IntegerField(
        default=0, blank=True, null=True
    )

    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    taxable_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    cgst_amount = models.DecimalField(max_digits=12, 
    decimal_places=2, 
    default=0)  # Added field tracking

    sgst_amount = models.DecimalField(max_digits=12, 
    decimal_places=2, 
    default=0)  # Added field tracking

    igst_amount = models.DecimalField(max_digits=12, 
    decimal_places=2, 
    default=0)  # Added field tracking

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.product.name

    def total_units(self):
        return self.qty + self.free_qty


    @transaction.atomic
    def save(self, *args, **kwargs):

        # Prevent calling full_clean() inside save block if it creates double-validation loop
        original_units = 0
        if self.pk:
            old_item = InvoiceItem.objects.get(pk=self.pk)
            original_units = old_item.total_units()
            
            # Revert old stock temporary for calculations
            old_batch = old_item.batch
            old_batch.stock_qty += original_units
            old_batch.save()

        required_stock = self.total_units()
        if required_stock > self.batch.stock_qty:
            raise ValidationError(f"Only {self.batch.stock_qty} units available")

        # 🛡️ Cast calculations to safeguard mathematical operations
        qty = int(self.qty or 0)
        rate = Decimal(str(self.rate or 0))
        discount = Decimal(str(self.discount or 0))

        self.taxable_value = (self.qty * self.rate) - self.discount
        self.gst_rate = self.product.gst_rate
        gst_amount = (self.taxable_value * self.gst_rate) / 100
        self.line_total = self.taxable_value + gst_amount

        # 🚀 NEW: Dynamic Interstate vs Intrastate tax router logic
        company = Company.objects.first()
        seller_state = company.state.strip().upper() if company and company.state else "BIHAR"
        buyer_state = self.invoice.customer.state.strip().upper()

        if seller_state == buyer_state:
            # Same State -> Split CGST + SGST (IGST is zero)
            self.cgst_amount = gst_amount / 2
            self.sgst_amount = gst_amount / 2
            self.igst_amount = Decimal("0.00")
        else:
            # Different State -> Full IGST applied (CGST/SGST are zero)
            self.cgst_amount = Decimal("0.00")
            self.sgst_amount = Decimal("0.00")
            self.igst_amount = gst_amount

        self.batch.stock_qty -= required_stock
        self.batch.save()

        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def delete(self, *args, **kwargs):
        self.batch.stock_qty += self.total_units()
        self.batch.save()
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.calculate_totals()

    #  NEW SECURED CODE BLOCK:
    def clean(self):
        if self.qty <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if self.rate < 0:
            raise ValidationError("Rate cannot be negative")

        # Ensure blank values evaluate to 0 instead of falling back to None
        qty = self.qty or 0
        free_qty = self.free_qty or 0

        # Allow adjustment room if updating existing items
        original_units = 0
        if self.pk:
            original_units = InvoiceItem.objects.get(pk=self.pk).total_units()

        # Safe calculation wrapper variables protected against None inputs
        required_stock = (qty + free_qty) - original_units
        if required_stock > self.batch.stock_qty:
            raise ValidationError(f"Only {self.batch.stock_qty + original_units} items available in stock")

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gst_no = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name


class PurchaseInvoice(models.Model):

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT
    )

    invoice_no = models.CharField(max_length=100)

    invoice_date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.invoice_no


class PurchaseItem(models.Model):

    purchase_invoice = models.ForeignKey(
        PurchaseInvoice,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    batch_no = models.CharField(max_length=50)

    expiry_date = models.DateField()

    qty = models.IntegerField()

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    ptr = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    pts = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    @transaction.atomic
    def save(self, *args, **kwargs):

        old_qty = 0

        if self.pk:

            old_qty = PurchaseItem.objects.get(
                pk=self.pk
            ).qty

        difference = self.qty - old_qty

        super().save(*args, **kwargs)


        batch, created = Batch.objects.get_or_create(
            product=self.product,
            batch_no=self.batch_no,
            defaults={
                'expiry_date': self.expiry_date,
                'mrp': self.mrp,
                'ptr': self.ptr,
                'pts': self.pts,
                'stock_qty': 0
                }
            )

        # Safe addition whether it is an update or a new record
        batch.stock_qty += difference
        batch.expiry_date = self.expiry_date
        batch.mrp = self.mrp
        batch.ptr = self.ptr
        batch.pts = self.pts
        batch.save()


class Payment(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference_no = models.CharField(
        max_length=100,
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    def __str__(self):
        return (
            f"{self.customer.name} - "
            f"{self.amount}"
        )

class SalesReturn(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT
    )

    return_date = models.DateField()

    remarks = models.TextField(
        blank=True
    )

    credit_amount = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0
    )

    def __str__(self):
        return f"Return {self.id}"

class SalesReturnItem(models.Model):

    sales_return = models.ForeignKey(
        SalesReturn,
        on_delete=models.CASCADE,
        related_name='items'
    )

    invoice_item = models.ForeignKey(
        InvoiceItem,
        on_delete=models.PROTECT
    )

    qty = models.IntegerField()

    def __str__(self):
        return str(self.invoice_item.product)

    @transaction.atomic
    def save(self, *args, **kwargs):

        batch = self.invoice_item.batch
        old_qty = 0

        if self.pk:
            old_item = SalesReturnItem.objects.get(pk=self.pk)
            old_qty = old_item.qty

        delta_qty = self.qty - old_qty
        batch.stock_qty += delta_qty
        batch.save()

        
        delta_value = Decimal(str(delta_qty)) * self.invoice_item.rate
        self.sales_return.credit_amount += delta_value
        self.sales_return.save()
        super().save(*args, **kwargs)

    def clean(self):

        if self.qty <= 0:
            raise ValidationError("Quantity must be greater than zero")

        sold_qty = self.invoice_item.qty
        previous_returns = SalesReturnItem.objects.filter(invoice_item=self.invoice_item)

        if self.pk:
            previous_returns = previous_returns.exclude(pk=self.pk)

        returned_qty = sum(item.qty for item in previous_returns)
        allowed_qty = sold_qty - returned_qty
        
        if self.qty > allowed_qty:
            raise ValidationError(f"Only {allowed_qty} units can be returned")

class PurchaseReturn(models.Model):

    purchase_invoice = models.ForeignKey(
        PurchaseInvoice,
        on_delete=models.PROTECT
    )

    return_date = models.DateField()

    remarks = models.TextField(
        blank=True
    )

    return_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"Purchase Return {self.id}"

class PurchaseReturnItem(models.Model):

    purchase_return = models.ForeignKey(
        PurchaseReturn,
        on_delete=models.CASCADE,
        related_name='items'
    )

    purchase_item = models.ForeignKey(
        PurchaseItem,
        on_delete=models.PROTECT
    )

    qty = models.IntegerField()

    def __str__(self):
        return str(
            self.purchase_item.product
        )

    @transaction.atomic
    def save(self, *args, **kwargs):

        batch = self.purchase_item.batch
        old_qty = 0

        if self.pk:
            old_qty = PurchaseReturnItem.objects.get(pk=self.pk).qty

        delta_qty = self.qty - old_qty

        if delta_qty > batch.stock_qty:
            raise ValidationError(f"Not enough stock available. Max can be returned extra: {batch.stock_qty}")

        batch.stock_qty -= delta_qty
        batch.save()

        delta_value = Decimal(str(delta_qty)) * self.purchase_item.ptr
        self.purchase_return.return_amount += delta_value
        self.purchase_return.save()

        super().save(*args, **kwargs)   

    def clean(self):
        if self.qty <= 0:
            raise ValidationError("Quantity must be greater than zero")