from django.urls import path
from . import views

urlpatterns = [
    path('api/users/<int:id>/biometric-status/',views.GetBiometricStatus.as_view()),
    path("api/users/<int:id>/face/",views.BiometricFace_.as_view())
]
