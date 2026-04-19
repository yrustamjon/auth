from django.urls import path
from . import views



urlpatterns = [


    path("api/switch-organization/", views.SwitchOrganization.as_view(), name="switch_organization"),
    path("api/organizations/", views.Organizations.as_view(), name="organizations"),
    path("api/organizations/<int:id>/", views.Organizations.as_view()),

    # =========================
    # TOKEN (AUTH)
    # =========================
    path("api/token/", views.GetActiveToken.as_view(), name="get_active_token"),

    # =========================
    # AGENT
    # =========================
    path("api/agent/activate/", views.ActivateAgent.as_view(), name="activate_agent"),

]