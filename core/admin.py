from django.contrib import admin
from .models import RateCard, RestrictedItem, ContactEnquiry

admin.site.register(RateCard)
admin.site.register(RestrictedItem)
admin.site.register(ContactEnquiry)
