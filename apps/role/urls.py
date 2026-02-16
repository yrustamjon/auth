from django.urls import path
from . import views

urlpatterns = [
    path('api/roles', views.RoleListView.as_view(), name='role_list'),  
]