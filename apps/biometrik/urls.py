from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('api/users/<int:id>/biometric-status/',views.GetBiometricStatus.as_view()),
    path("api/users/<int:id>/face/",views.BiometricFace_.as_view()),

    path('api/users/<int:id>/fingerprint-session/', FingerprintSessionCreateView.as_view()),
    path('api/fingerprint-session/<str:token>/status/', FingerprintSessionStatusView.as_view()),
    path('api/fingerprint-session/<str:token>/save/', FingerprintSaveView.as_view()),


    path("api/users/<int:id>/fingerprint/",views.BiometricFingerprint_.as_view())
]
