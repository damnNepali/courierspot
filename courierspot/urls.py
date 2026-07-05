from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.static import serve

from accounts import views as acc
from core import views as core_v
from operations import views as ops
from tracking import views as trk

urlpatterns = [
    # public website
    path('', core_v.home, name='home'),
    path('rates/', core_v.rates_page, name='rates_page'),
    path('contact/', core_v.contact_submit, name='contact_submit'),
    path('track/', trk.track_page, name='public_track_search'),
    path('track/<str:tracking_id>/', trk.track_page, name='public_track'),

    # customer accounts
    path('accounts/login/', auth_views.LoginView.as_view(template_name='public/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/signup/', acc.signup, name='signup'),
    path('accounts/redirect/', acc.post_login_redirect, name='post_login_redirect'),
    path('my-parcels/', core_v.customer_dashboard, name='customer_dashboard'),

    # staff / SaaS panel
    path('panel/', ops.dashboard, name='panel_dashboard'),
    path('panel/shipments/new/', ops.shipment_create, name='shipment_create'),
    path('panel/sender-lookup/', ops.sender_lookup, name='sender_lookup'),
    path('panel/parcels/', ops.parcel_list, name='parcel_list'),
    path('panel/parcels/<int:pk>/', ops.parcel_detail, name='parcel_detail'),
    path('panel/invoices/<int:pk>/print/', ops.invoice_print, name='invoice_print'),
    path('panel/expenses/', ops.expenses, name='expenses'),

    # owner-only
    path('panel/finance/', ops.finance, name='finance'),
    path('panel/branches/', ops.branches, name='branches'),
    path('panel/staff/new/', ops.staff_create, name='staff_create'),
    path('panel/rates/', ops.rates_manage, name='rates_manage'),
    path('panel/restricted/add/', ops.restricted_add, name='restricted_add'),

    # API
    path('api/track/<str:tracking_id>/', trk.TrackParcelAPI.as_view(), name='api_track'),

    # Django admin (developer backstage)
    path('django-admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]