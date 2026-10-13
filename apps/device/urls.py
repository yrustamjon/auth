from django.urls import path
from . import views
from . import browser_views
from . import frontend_views

from .removal_views import IssueRemovalCode, RemovalAction, InstallStatus, ActivationStatus

urlpatterns = [
    path('api/devices/<int:device_id>/removal-code/', IssueRemovalCode.as_view()),
    path('api/agent/removal/check/', RemovalAction.as_view(action='check')),
    path('api/agent/removal/begin/', RemovalAction.as_view(action='begin')),
    path('api/agent/removal/status/', RemovalAction.as_view(action='status')),
    path('api/agent/removal/complete/', RemovalAction.as_view(action='complete')),
    path('api/agent/install/status/', InstallStatus.as_view()),
    path('api/agent/activate/status/', ActivationStatus.as_view()),
    path('api/devices/browser-enrollment/claim/', frontend_views.claim_json),
    path('api/devices/browser-enrollment/approval/', frontend_views.approval_json),
    path('device/scan', browser_views.scan_page, name='device_scan'),
    path('device-enroll/<str:token>', browser_views.qr_entry, name='device_enroll_entry'),
    path('device-enroll/approval/', browser_views.approval_page, name='device_enroll_approval'),
    path('devices/scan-qr/', browser_views.admin_scanner_page, name='device_admin_scanner'),
    path('devices/add/qr', browser_views.admin_scanner_page, name='device_add_via_qr'),
    path('api/devices/browser-enrollment/session/', browser_views.session_create, name='browser_enrollment_create'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/', browser_views.session_status, name='browser_enrollment_status'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/identity/', browser_views.session_identity, name='browser_enrollment_identity'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/helper/<str:platform>/', browser_views.session_helper, name='browser_enrollment_helper'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/binary/<str:platform>/<str:architecture>/', browser_views.session_binary, name='browser_enrollment_binary'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/approve/', browser_views.session_approve, name='browser_enrollment_approve'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/reject/', browser_views.session_reject, name='browser_enrollment_reject'),
    path('api/devices/browser-enrollment/session/<uuid:session_id>/cancel/', browser_views.session_cancel, name='browser_enrollment_cancel'),
    path('api/devices', views.DeviceView.as_view(), name='device_list'),
    path('api/devices/<int:device_id>/', views.DeviceView.as_view(), name='device_detail'),
    path('api/agent/check-pc/',views.DeviceCheck.as_view()),
]
