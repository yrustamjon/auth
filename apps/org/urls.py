from django.urls import path
from . import views



urlpatterns = [


    path("api/switch-organization/", views.SwitchOrganization.as_view(), name="switch_organization"),



]