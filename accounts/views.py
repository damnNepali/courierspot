from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import CustomerSignupForm


def signup(request):
    """Customer self-signup. Details are saved in the database;
    afterwards they can log in and track all their parcels."""
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('customer_dashboard')
    else:
        form = CustomerSignupForm()
    return render(request, 'public/signup.html', {'form': form})


@login_required
def post_login_redirect(request):
    """Send each role to its own home after login."""
    if request.user.is_panel_user:
        return redirect('panel_dashboard')
    return redirect('customer_dashboard')
