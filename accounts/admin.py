from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'role', 'branch', 'phone')
    fieldsets = UserAdmin.fieldsets + ((' Bharosa', {'fields': ('role', 'branch', 'phone', 'address')}),)
