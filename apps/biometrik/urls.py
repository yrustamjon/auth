from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('api/users/<int:id>/biometric-status/',views.GetBiometricStatus.as_view()),
    path("api/users/<int:id>/face/",views.BiometricFace_.as_view()),

    path("api/fingerprint/phone/start/", FingerprintPhoneStartView.as_view()),
    path('api/fingerprint/phone/submit/',FingerprintPhoneSubmitView.as_view()),
    path(
        "api/fingerprint/phone/status/<uuid:session_id>/",
        FingerprintPhoneStatusView.as_view()
    ),
    path("api/users/<int:id>/fingerprint/", BiometricFingerprintListView.as_view()),
    path("api/users/<int:user_id>/fingerprint/<int:id>/", BiometricFingerprintListView.as_view()),


    path(
        "mobile/fingerprint/<uuid:session_id>/",
        MobileFingerprintView.as_view()
    ),

    path("api/face/phone/check/", PhoneFaceChecker.as_view())
    
]
