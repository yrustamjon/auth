from django.urls import path
from . import views

urlpatterns = [ 
    path('api/access-logs', views.LogView.as_view(), name='log_list'),
]