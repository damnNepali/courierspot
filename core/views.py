from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import RateCard, RestrictedItem, ContactEnquiry
from operations.models import Branch
from tracking.models import Parcel


def home(request):
    return render(request, 'public/home.html', {
        'rates': RateCard.objects.filter(is_active=True)[:8],
        'branches': Branch.objects.filter(is_active=True),
    })


def rates_page(request):
    return render(request, 'public/rates.html', {
        'rates': RateCard.objects.filter(is_active=True),
        'restricted': RestrictedItem.objects.all(),
        'branches': Branch.objects.filter(is_active=True),
    })


def contact_submit(request):
    """Public contact form → saved in DB; if a tracking number was given,
    the enquiry is linked straight to that parcel."""
    if request.method == 'POST':
        tn = request.POST.get('tracking_number', '').strip()
        ContactEnquiry.objects.create(
            name=request.POST.get('name', '').strip(),
            email=request.POST.get('email', '').strip(),
            tracking_number=tn,
            message=request.POST.get('message', '').strip(),
            parcel=Parcel.objects.filter(tracking_id__iexact=tn).first() if tn else None,
        )
        messages.success(request, "Message sent — our team will reply soon.")
    return redirect('home')


@login_required
def customer_dashboard(request):
    """Customer sees every parcel matching their phone or email."""
    u = request.user
    parcels = Parcel.objects.none()
    if u.phone or u.email:
        from django.db.models import Q
        q = Q()
        if u.phone:
            q |= Q(sender_phone=u.phone) | Q(receiver_phone=u.phone)
        if u.email:
            q |= Q(sender_email__iexact=u.email)
        parcels = Parcel.objects.filter(q)
    return render(request, 'public/customer_dashboard.html', {'parcels': parcels})
