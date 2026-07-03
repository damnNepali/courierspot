from django.contrib import admin
from .models import Parcel, TrackingEvent

admin.site.register(Parcel)
admin.site.register(TrackingEvent)
