from decimal import Decimal
from django.conf import settings
from django.db import models

CUSTOMS_TAX = Decimal('1800.00')  # compulsory on EVERY parcel — business rule


class Branch(models.Model):
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=160, help_text='City / area, e.g. Kathmandu — Dhumbarahi')
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.name


class Invoice(models.Model):
    """One invoice per parcel. Money fields are snapshots — if the rate
    changes later, old invoices keep the price the customer actually paid."""
    parcel = models.OneToOneField('tracking.Parcel', on_delete=models.PROTECT, related_name='invoice')
    invoice_no = models.CharField(max_length=20, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='invoices')
    total_weight = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # legacy, no longer set — boxes have their own rate now
    weight_charge = models.DecimalField(max_digits=12, decimal_places=2)
    additional_charges_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    customs_tax = models.DecimalField(max_digits=12, decimal_places=2, default=CUSTOMS_TAX)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def subtotal(self):
        """Weight + additional charges, before customs tax."""
        return self.weight_charge + self.additional_charges_total

    def __str__(self):
        return self.invoice_no

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} ×{self.quantity}"

class Expense(models.Model):
    CATEGORIES = [('FUEL', 'Fuel / Transport'), ('RENT', 'Rent'), ('SALARY', 'Salary'),
                  ('CARRIER', 'Carrier Charges'), ('SUPPLIES', 'Supplies'), ('OTHER', 'Other')]
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='expenses')
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=12, choices=CATEGORIES, default='OTHER')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    bill_image = models.ImageField(upload_to='bills/', blank=True, null=True,
                                   help_text='Photo/scan of the bill or invoice')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} — NPR {self.amount}"


class AuditLog(models.Model):
    """Every important change is recorded: who, what, when.
    Owner can review this — protection in a cash business."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"


def log(user, action):
    AuditLog.objects.create(user=user, action=action)

class Box(models.Model):
    parcel = models.ForeignKey('tracking.Parcel', on_delete=models.CASCADE, related_name='boxes')
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    rate_per_kg = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def weight_charge(self):
        return (self.weight * self.rate_per_kg).quantize(Decimal('0.01'))

    @property
    def charges_total(self):
        return sum((c.price for c in self.charges.all()), Decimal('0.00'))

    @property
    def total(self):
        return self.weight_charge + self.charges_total

    def __str__(self):
        return f"Box for {self.parcel.tracking_id}"


class BoxItem(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)
    unit_value_usd = models.DecimalField(max_digits=10, decimal_places=2,
                                         default=Decimal('0.00'))

    @property
    def subtotal_usd(self):
        return (self.unit_value_usd * self.quantity).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.name} ×{self.quantity}"

class BoxCharge(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name='charges')
    name = models.CharField(max_length=160, blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.name or 'Charge'} — NPR {self.price}"