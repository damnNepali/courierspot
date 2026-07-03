from django.contrib import admin
from .models import Branch, Invoice, InvoiceItem, Expense, AuditLog

admin.site.register(Branch)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Expense)
admin.site.register(AuditLog)
