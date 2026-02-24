from django.urls import path
from . import views

urlpatterns = [
    path('api/devices', views.DeviceView.as_view(), name='device_list'),
    path('api/devices/<int:device_id>/', views.DeviceView.as_view(), name='device_detail'),
]