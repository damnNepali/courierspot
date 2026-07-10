import random
import string
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Parcel(models.Model):
    class Status(models.TextChoices):
        ORDER_CREATED = 'ORDER_CREATED', '📦 Order Created'
        COLLECTED = 'COLLECTED', '✅ Parcel Collected'
        RECEIVED_BRANCH = 'RECEIVED_BRANCH', '🏢 Received at Courier Spot Branch'
        PROCESSED = 'PROCESSED', '📋 Shipment Processed'
        TRANSFERRED_HUB = 'TRANSFERRED_HUB', '🚚 Transferred to Kathmandu Export Hub'
        EXPORT_CUSTOMS = 'EXPORT_CUSTOMS', '🛃 Export Customs Clearance'
        DEPARTED = 'DEPARTED', '✈️ Departed from Nepal'
        IN_TRANSIT = 'IN_TRANSIT', '🌍 In Transit'
        ARRIVED_DEST = 'ARRIVED_DEST', 'Arrived at Destination Country'
        IMPORT_CUSTOMS = 'IMPORT_CUSTOMS', '🛃 Import Customs Clearance'
        TRANSFERRED_LOCAL = 'TRANSFERRED_LOCAL', '🚛 Transferred to Local Delivery Partner'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', '🚚 Out for Delivery'
        DELIVERED = 'DELIVERED', '✅ Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    CARRIERS = [('FEDEX', 'FedEx'), ('DHL', 'DHL Express'), ('ARAMEX', 'Aramex'),
                ('SKYNET', 'SkyNet'), ('DPD', 'DPD')]

    tracking_id = models.CharField(max_length=20, unique=True, editable=False)
    branch = models.ForeignKey('operations.Branch', on_delete=models.PROTECT, related_name='parcels')

    # Sender (From)
    sender_name = models.CharField(max_length=120)
    sender_phone = models.CharField(max_length=20)
    sender_address = models.CharField(max_length=255)
    sender_email = models.EmailField(blank=True)

    # Receiver (To)
    receiver_name = models.CharField(max_length=120)
    receiver_phone = models.CharField(max_length=30)
    receiver_address = models.CharField(max_length=255)
    destination_country = models.CharField(max_length=80)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDER_CREATED)
    carrier = models.CharField(max_length=10, choices=CARRIERS, blank=True)
    carrier_tracking_no = models.CharField(max_length=60, blank=True)

    qr_code = models.ImageField(upload_to='qr/', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    # Draft support: a draft has NO invoice, NO tracking events and is hidden
    # from public tracking. Finalising it creates the invoice and locks pricing.
    is_draft = models.BooleanField(default=False)
    # Customs tax typed while the shipment was still a draft, so it is
    # remembered when the draft is reopened (moves onto the Invoice at finalise).
    draft_customs_tax = models.DecimalField(max_digits=12, decimal_places=2,
                                            null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.tracking_id

    @staticmethod
    def next_tracking_id():
        """CSP + YYMMDD + 6 random uppercase-alphanumeric chars, e.g. CSP250703A8K9P2."""
        while True:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            tracking_id = f'CSP{timezone.now():%y%m%d}{suffix}'
            if not Parcel.objects.filter(tracking_id=tracking_id).exists():
                return tracking_id

    def tracking_url(self):
        return settings.SITE_URL + reverse('public_track', args=[self.tracking_id])

    def generate_qr(self):
        """Make a QR pointing at this parcel's public tracking page."""
        import qrcode
        img = qrcode.make(self.tracking_url(), box_size=8, border=2)
        buf = BytesIO()
        img.save(buf, format='PNG')
        self.qr_code.save(f'{self.tracking_id}.png', ContentFile(buf.getvalue()), save=False)


class TrackingEvent(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=Parcel.Status.choices)
    location = models.CharField(max_length=160)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.parcel.tracking_id}: {self.get_status_display()}"