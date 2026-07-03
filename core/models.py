from django.db import models


class RateCard(models.Model):
    """Country rates — edited by the owner, shown live on the public website."""
    country = models.CharField(max_length=80, unique=True)
    flag = models.CharField(max_length=8, blank=True, help_text='Emoji flag, e.g. 🇺🇸')
    rate_per_kg = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = models.CharField(max_length=30, help_text='e.g. 5–7 days')
    carriers = models.CharField(max_length=120, help_text='e.g. FedEx · DHL Express')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['country']

    def __str__(self):
        return f"{self.country} — NPR {self.rate_per_kg}/kg"


class RestrictedItem(models.Model):
    country = models.CharField(max_length=80)
    item = models.CharField(max_length=160)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['country', 'item']

    def __str__(self):
        return f"{self.country}: {self.item}"


class ContactEnquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    tracking_number = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    parcel = models.ForeignKey('tracking.Parcel', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Contact enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.created_at:%d %b %Y}"
