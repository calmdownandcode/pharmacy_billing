from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    gst_no = models.CharField(max_length=20)
    drug_license_no = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    gst_no = models.CharField(max_length=20, blank=True)
    drug_license_no = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=100)

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

    class Meta:
        unique_together = (
            'product',
            'batch_no'
        )

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
        total_gst = Decimal("0.00")

        for item in items:
            taxable += item.taxable_value
            total_gst += item.line_total - item.taxable_value

        self.taxable_amount = taxable
        self.cgst_amount = total_gst / 2
        self.sgst_amount = total_gst / 2

        self.net_amount = taxable + total_gst

        self.save(update_fields=[
            'taxable_amount',
            'cgst_amount',
            'sgst_amount',
            'net_amount'
        ])

    def save(self, *args, **kwargs):

        if not self.invoice_number:

            last_invoice = Invoice.objects.order_by('-id').first()

            if last_invoice:
                next_number = last_invoice.id + 1
            else:
                next_number = 1

            self.invoice_number = f"INV-{next_number:05d}"

        super().save(*args, **kwargs)

    def calculate_totals(self):

        taxable = Decimal("0.00")
        total_gst = Decimal("0.00")

        for item in self.items.all():

            taxable += item.taxable_value

            total_gst += (
                item.line_total -
                item.taxable_value
            )

        self.taxable_amount = taxable

        self.cgst_amount = total_gst / 2

        self.sgst_amount = total_gst / 2

        self.net_amount = (
            taxable +
            total_gst
        )

        super().save(
            update_fields=[
                "taxable_amount",
                "cgst_amount",
                "sgst_amount",
                "net_amount"
            ]
        )


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
        default=0
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

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.product.name

    def total_units(self):
        return self.qty + self.free_qty

    def save(self, *args, **kwargs):

        self.full_clean()

        if self.pk:
            old_item = InvoiceItem.objects.get(pk=self.pk)

            old_batch = old_item.batch
            old_batch.stock_qty += old_item.total_units()
            old_batch.save()

        required_stock = self.total_units()

        if required_stock > self.batch.stock_qty:
            raise ValidationError(
                f"Only {self.batch.stock_qty} units available"
            )

        self.taxable_value = (
            self.qty * self.rate
        ) - self.discount

        self.gst_rate = self.product.gst_rate

        gst_amount = (
            self.taxable_value * self.gst_rate
        ) / 100

        self.line_total = (
            self.taxable_value + gst_amount
        )

        self.batch.stock_qty -= required_stock
        self.batch.save()

        super().save(*args, **kwargs)
        self.invoice.calculate_totals()


    def clean(self):
        required_stock = self.qty + self.free_qty

        if required_stock > self.batch.stock_qty:
            raise ValidationError(
                f"Only {self.batch.stock_qty} items available in stock"
            )


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

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:

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

            batch.stock_qty += self.qty

            batch.expiry_date = self.expiry_date
            batch.mrp = self.mrp
            batch.ptr = self.ptr
            batch.pts = self.pts

            batch.save()