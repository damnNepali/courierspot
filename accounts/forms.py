from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomerSignupForm(UserCreationForm):
    """Public signup — always creates a CUSTOMER account."""
    first_name = forms.CharField(max_length=80, label='Full name')
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'phone', 'address')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.CUSTOMER
        if commit:
            user.save()
        return user


class StaffCreateForm(UserCreationForm):
    """Owner/branch-admin creates panel accounts (staff or branch admin)."""
    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'phone', 'role', 'branch')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Panel accounts only — customers sign up themselves on the website.
        self.fields['role'].choices = [
            (User.Roles.BRANCH_ADMIN, 'Branch Admin'),
            (User.Roles.STAFF, 'Staff'),
        ]
