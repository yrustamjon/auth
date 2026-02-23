from django.urls import path
from . import views



urlpatterns = [


    path("api/switch-organization/", views.SwitchOrganization.as_view(), name="switch_organization"),
    path("api/organizations/", views.Organizations.as_view(), name="organizations"),
    path("api/organizations/<int:id>/", views.Organizations.as_view()),



]