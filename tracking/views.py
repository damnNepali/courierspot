from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Parcel

STATUS_ORDER = ['ORDER_CREATED', 'COLLECTED', 'RECEIVED_BRANCH', 'PROCESSED',
    'TRANSFERRED_HUB', 'EXPORT_CUSTOMS', 'DEPARTED', 'IN_TRANSIT',
    'ARRIVED_DEST', 'IMPORT_CUSTOMS', 'TRANSFERRED_LOCAL',
    'OUT_FOR_DELIVERY', 'DELIVERED',]


def build_timeline(parcel):
    """Four fixed steps; each is done/current/pending based on real events."""
    events = {e.status: e for e in parcel.events.all()}
    reached = STATUS_ORDER.index(parcel.status) if parcel.status in STATUS_ORDER else -1
    timeline = []
    for i, status in enumerate(STATUS_ORDER):
        e = events.get(status)
        timeline.append({
            'status': status,
            'label': dict(Parcel.Status.choices)[status],
            'done': i <= reached,
            'when': e.created_at if e else None,
            'location': e.location if e else '',
            'note': e.note if e else '',
        })
    return timeline


def track_page(request, tracking_id=''):
    """Public tracking page — also the target of the invoice QR code."""
    tid = tracking_id or request.GET.get('id', '')
    parcel = Parcel.objects.filter(tracking_id__iexact=tid.strip(), is_draft=False).first() if tid else None
    return render(request, 'public/track.html', {
        'parcel': parcel,
        'searched': bool(tid),
        'tid': tid,
        'timeline': build_timeline(parcel) if parcel else [],
    })


class TrackParcelAPI(APIView):
    """Public DRF endpoint: GET /api/track/<tracking_id>/"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, tracking_id):
        parcel = Parcel.objects.filter(tracking_id__iexact=tracking_id, is_draft=False).first()
        if not parcel:
            return Response({'found': False}, status=404)
        return Response({
            'found': True,
            'tracking_id': parcel.tracking_id,
            'status': parcel.status,
            'destination': parcel.destination_country,
            'carrier': parcel.get_carrier_display() if parcel.carrier else None,
            'carrier_tracking_no': parcel.carrier_tracking_no or None,
            'events': [{
                'status': e.get_status_display(), 'location': e.location,
                'note': e.note, 'at': e.created_at.isoformat(),
            } for e in parcel.events.all()],
        })
