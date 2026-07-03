from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role and an optional branch.

    Why: one login system for owner, branch staff and customers —
    the role decides which panel and which data they can see.
    """
    class Roles(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Super Admin (Owner)'
        BRANCH_ADMIN = 'BRANCH_ADMIN', 'Branch Admin'
        STAFF = 'STAFF', 'Staff'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CUSTOMER)
    branch = models.ForeignKey('operations.Branch', null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    @property
    def is_owner(self):
        return self.role == self.Roles.SUPERADMIN

    @property
    def is_panel_user(self):
        return self.role in (self.Roles.SUPERADMIN, self.Roles.BRANCH_ADMIN, self.Roles.STAFF)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
