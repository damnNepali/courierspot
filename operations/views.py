from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Box, BoxItem, BoxCharge

from accounts.forms import StaffCreateForm
from accounts.models import User
from core.models import RateCard, RestrictedItem, ContactEnquiry
from tracking.models import Parcel, TrackingEvent
from .models import AuditLog, Branch, CUSTOMS_TAX, Expense, Invoice, InvoiceItem, log
import re

# ---------- permissions ----------

def panel_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *a, **kw):
        if not request.user.is_panel_user:
            return HttpResponseForbidden('Staff panel access only.')
        return view(request, *a, **kw)
    return wrapper


def owner_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *a, **kw):
        if not request.user.is_owner:
            return HttpResponseForbidden('Owner access only.')
        return view(request, *a, **kw)
    return wrapper


def branch_scope(qs, user):
    """Owner sees all branches; everyone else only their own."""
    return qs if user.is_owner else qs.filter(branch=user.branch)


# ---------- dashboard ----------

@panel_required
def dashboard(request):
    today = timezone.localdate()
    parcels = branch_scope(Parcel.objects.all(), request.user)
    invoices = branch_scope(Invoice.objects.all(), request.user)
    ctx = {
        'today_parcels': parcels.filter(created_at__date=today).count(),
        'total_parcels': parcels.count(),
        'in_transit': parcels.filter(status=Parcel.Status.IN_TRANSIT).count(),
        'today_income': invoices.filter(created_at__date=today).aggregate(s=Sum('grand_total'))['s'] or 0,
        'recent': parcels.select_related('branch')[:8],
        'enquiries': ContactEnquiry.objects.filter(is_resolved=False)[:5] if request.user.is_owner else None,
    }
    return render(request, 'panel/dashboard.html', ctx)


# ---------- new shipment (the heart of the SaaS) ----------


@panel_required
def shipment_create(request):
    rates = RateCard.objects.filter(is_active=True)
    if request.method == 'POST':
        try:
            country = request.POST['destination_country']
            rate_card = rates.get(country=country)  # kept for display/validation; each box sets its own rate

            box_indices = sorted({
                int(m.group(1))
                for k in request.POST.keys()
                for m in [re.match(r'box\[(\d+)\]\[weight\]', k)] if m
            })
            if not box_indices:
                raise ValueError('Add at least one box.')

            boxes_data = []
            any_item = False
            for i in box_indices:
                weight = Decimal(request.POST[f'box[{i}][weight]'])
                rate = Decimal(request.POST[f'box[{i}][rate]'])

                item_names = request.POST.getlist(f'box[{i}][item_name][]')
                item_qtys = request.POST.getlist(f'box[{i}][item_qty][]')
                items = [(n.strip(), int(q)) for n, q in zip(item_names, item_qtys) if n.strip()]
                if items:
                    any_item = True

                charge_names = request.POST.getlist(f'box[{i}][charge_name][]')
                charge_weights = request.POST.getlist(f'box[{i}][charge_weight][]')
                charge_prices = request.POST.getlist(f'box[{i}][charge_price][]')
                charges = [
                    (cn.strip(), Decimal(cw) if cw.strip() else None, Decimal(cp))
                    for cn, cw, cp in zip(charge_names, charge_weights, charge_prices)
                    if cp.strip()
                ]

                boxes_data.append({'weight': weight, 'rate': rate, 'items': items, 'charges': charges})

            if not any_item:
                raise ValueError('Add at least one item.')

            total_weight = sum(b['weight'] for b in boxes_data)
            weight_charge = sum((b['weight'] * b['rate']).quantize(Decimal('0.01')) for b in boxes_data)
            additional_charges_total = sum(
                (c[2] for b in boxes_data for c in b['charges']), Decimal('0.00')
            )
            grand_total = weight_charge + additional_charges_total + CUSTOMS_TAX

            branch = request.user.branch or Branch.objects.filter(is_active=True).first()

            with transaction.atomic():  # all-or-nothing: parcel+invoice+boxes+items+charges+event+QR
                parcel = Parcel(
                    tracking_id=Parcel.next_tracking_id(), branch=branch,
                    sender_name=request.POST['sender_name'], sender_phone=request.POST['sender_phone'],
                    sender_address=request.POST['sender_address'], sender_email=request.POST.get('sender_email', ''),
                    receiver_name=request.POST['receiver_name'], receiver_phone=request.POST['receiver_phone'],
                    receiver_address=request.POST['receiver_address'], destination_country=country,
                    created_by=request.user,
                )
                parcel.generate_qr()
                parcel.save()

                for b in boxes_data:
                    box = Box.objects.create(parcel=parcel, weight=b['weight'], rate_per_kg=b['rate'])
                    BoxItem.objects.bulk_create([
                        BoxItem(box=box, name=n, quantity=q) for n, q in b['items']
                    ])
                    BoxCharge.objects.bulk_create([
                        BoxCharge(box=box, name=cn, weight=cw, price=cp) for cn, cw, cp in b['charges']
                    ])

                seq_year = timezone.now().year
                last = Invoice.objects.filter(invoice_no__startswith=f'INV-{seq_year}-').order_by('-id').first()
                seq = int(last.invoice_no.split('-')[-1]) + 1 if last else 1
                invoice = Invoice.objects.create(
                    parcel=parcel, invoice_no=f'INV-{seq_year}-{seq:06d}', branch=branch,
                    total_weight=total_weight, weight_charge=weight_charge,
                    additional_charges_total=additional_charges_total,
                    customs_tax=CUSTOMS_TAX, grand_total=grand_total, created_by=request.user,
                )
                TrackingEvent.objects.create(
                    parcel=parcel, status=Parcel.Status.ORDER_CREATED,
                    location=branch.location, note='Parcel registered at branch',
                    created_by=request.user,
                )
                log(request.user, f'Created shipment {parcel.tracking_id} / {invoice.invoice_no} '
                                  f'(NPR {grand_total}) at {branch.name}')
            messages.success(request, f'Shipment {parcel.tracking_id} created.')
            return redirect('invoice_print', invoice.id)
        except (KeyError, ValueError, InvalidOperation, RateCard.DoesNotExist) as e:
            messages.error(request, f'Could not save shipment: {e}')
    return render(request, 'panel/shipment_form.html', {'rates': rates, 'customs_tax': CUSTOMS_TAX})
@panel_required
def sender_lookup(request):
    """Auto-fill: if this phone has shipped before, return their details."""
    phone = request.GET.get('phone', '').strip()
    p = Parcel.objects.filter(sender_phone=phone).order_by('-created_at').first() if phone else None
    if not p:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, 'name': p.sender_name,
                         'address': p.sender_address, 'email': p.sender_email})


# ---------- parcels ----------

@panel_required
def parcel_list(request):
    q = request.GET.get('q', '').strip()
    parcels = branch_scope(Parcel.objects.select_related('branch', 'invoice'), request.user)
    if q:
        parcels = parcels.filter(
            Q(tracking_id__icontains=q) | Q(sender_phone__icontains=q) |
            Q(sender_name__icontains=q) | Q(receiver_name__icontains=q) |
            Q(invoice__invoice_no__icontains=q))
    return render(request, 'panel/parcel_list.html', {'parcels': parcels[:100], 'q': q})


@panel_required
def parcel_detail(request, pk):
    parcel = get_object_or_404(branch_scope(Parcel.objects.all(), request.user), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'status':
            new = request.POST['status']
            old = parcel.status
            if new != old:
                parcel.status = new
                parcel.save()
                TrackingEvent.objects.create(
                    parcel=parcel, status=new,
                    location=request.POST.get('location') or parcel.branch.location,
                    note=request.POST.get('note', ''), created_by=request.user)
                log(request.user, f'{parcel.tracking_id}: status {old} → {new}')
                messages.success(request, 'Status updated.')
        elif action == 'carrier':
            parcel.carrier = request.POST['carrier']
            parcel.carrier_tracking_no = request.POST.get('carrier_tracking_no', '')
            parcel.save()
            log(request.user, f'{parcel.tracking_id}: handed to {parcel.get_carrier_display()} '
                              f'({parcel.carrier_tracking_no})')
            messages.success(request, 'Carrier handover saved.')
        return redirect('parcel_detail', pk=pk)
    return render(request, 'panel/parcel_detail.html',
                  {'parcel': parcel, 'statuses': Parcel.Status.choices, 'carriers': Parcel.CARRIERS})


@panel_required
def invoice_print(request, pk):
    invoice = get_object_or_404(branch_scope(Invoice.objects.select_related('parcel', 'branch'),
                                             request.user), pk=pk)
    return render(request, 'panel/invoice_print.html', {'inv': invoice})


# ---------- expenses ----------

@panel_required
def expenses(request):
    if request.method == 'POST':
        Expense.objects.create(
            branch=request.user.branch or Branch.objects.first(),
            description=request.POST['description'], category=request.POST['category'],
            amount=Decimal(request.POST['amount']), date=request.POST['date'] or date.today(),
            bill_image=request.FILES.get('bill_image'), created_by=request.user)
        log(request.user, f"Expense added: {request.POST['description']} NPR {request.POST['amount']}")
        messages.success(request, 'Expense recorded.')
        return redirect('expenses')
    items = branch_scope(Expense.objects.select_related('branch'), request.user)[:100]
    total = branch_scope(Expense.objects.all(), request.user).aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'panel/expenses.html',
                  {'expenses': items, 'total': total, 'categories': Expense.CATEGORIES})


# ---------- owner-only: finance, branches, staff, rates ----------

@owner_required
def finance(request):
    """Income − expenses per branch. ONLY the owner ever sees this."""
    rows = []
    for b in Branch.objects.all():
        income = b.invoices.aggregate(s=Sum('grand_total'))['s'] or Decimal('0')
        spent = b.expenses.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        rows.append({'branch': b, 'income': income, 'spent': spent, 'balance': income - spent})
    totals = {
        'income': sum(r['income'] for r in rows),
        'spent': sum(r['spent'] for r in rows),
        'balance': sum(r['balance'] for r in rows),
    }
    return render(request, 'panel/finance.html',
                  {'rows': rows, 'totals': totals, 'audit': AuditLog.objects.select_related('user')[:30]})


@owner_required
def branches(request):
    if request.method == 'POST':
        Branch.objects.create(
            name=request.POST['name'], location=request.POST['location'],
            address=request.POST['address'], phone=request.POST['phone'],
            email=request.POST.get('email', ''))
        log(request.user, f"Branch created: {request.POST['name']}")
        messages.success(request, 'Branch created.')
        return redirect('branches')
    return render(request, 'panel/branches.html',
                  {'branches': Branch.objects.all(), 'staff': User.objects.exclude(role='CUSTOMER')})


@owner_required
def staff_create(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        u = form.save()
        log(request.user, f'Panel account created: {u.username} ({u.get_role_display()})')
        messages.success(request, f'Account for {u.username} created.')
        return redirect('branches')
    return render(request, 'panel/staff_form.html', {'form': form})


@owner_required
def rates_manage(request):
    if request.method == 'POST':
        RateCard.objects.update_or_create(
            country=request.POST['country'],
            defaults={'rate_per_kg': Decimal(request.POST['rate_per_kg']),
                      'delivery_days': request.POST['delivery_days'],
                      'carriers': request.POST['carriers'],
                      'flag': request.POST.get('flag', '')})
        log(request.user, f"Rate saved: {request.POST['country']} NPR {request.POST['rate_per_kg']}/kg")
        messages.success(request, 'Rate saved — public website updated instantly.')
        return redirect('rates_manage')
    return render(request, 'panel/rates.html',
                  {'rates': RateCard.objects.all(), 'restricted': RestrictedItem.objects.all()})


@owner_required
def restricted_add(request):
    if request.method == 'POST':
        RestrictedItem.objects.create(country=request.POST['country'],
                                      item=request.POST['item'],
                                      note=request.POST.get('note', ''))
        messages.success(request, 'Restricted item added.')
    return redirect('rates_manage')
