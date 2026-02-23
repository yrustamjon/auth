from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.models import *
from apps.org.models import *


class SwitchOrganization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("SwitchOrganization request data:", request.data)
        org_id = request.data.get("organization_id")

        
        if not request.user.organizations.filter(id=org_id).exists():
            return Response({"detail": "Forbidden"}, status=403)


        request.session["current_org_id"] = org_id
        request.session.save()

        return Response({"ok": True})

class Organizations(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,id=None):
        if id:
            orgs = Organization.objects.filter(id=id)
            return Response({
                "id": orgs[0].id,
                "name": orgs[0].name,
                "admin_count": AdminUser.objects.filter(organizations=orgs[0]).count(),
                "slug": orgs[0].slug,
                "active": orgs[0].is_active,
                "created_at": orgs[0].created_at,
            })
        orgs = Organization.objects.all()
        orgs_data = [
                {
                    "id": org.id,
                    "name": org.name,
                    "admin_count": AdminUser.objects.filter(organizations=org).count(),
                    "slug": org.slug,
                    "active": org.is_active,
                    "created_at": org.created_at,
                }
                for org in orgs if not org.slug == "system"
            ]
        return Response(orgs_data)
    
    def patch(self, request, id):
        active = request.data.get("active")
        print(f"Updating organization with id", id, "to active:", active)
        
        if "name" in request.data or "slug" in request.data:
            print(request.data)
            slug = request.data.get("slug")
            name = request.data.get("name")
            
            if not slug or not name:
                return Response({"detail": "Name and slug are required"}, status=400)
            org = Organization.objects.filter(id=id).first()
            if not org:
                return Response({"detail": "Organization not found"}, status=404)
            org.name = name
            org.slug = slug
            org.is_active = active
            org.save()
            return Response({"ok": True})
        org = Organization.objects.filter(id=id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=404)
        org.is_active = active
        org.save()
        return Response({"ok": True})
        
        


    def post(self, request):
        name = request.data.get("name")
        slug = request.data.get("slug")

        if not name or not slug:
            return Response({"detail": "Name and slug are required"}, status=400)

        if Organization.objects.filter(slug=slug).exists():
            return Response({"detail": "Organization with this slug already exists"}, status=400)

        org = Organization.objects.create(name=name, slug=slug)


        return Response({
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "active": org.is_active,
            "created_at": org.created_at,
        })


    def delete(self, request, id):
        org = Organization.objects.filter(id=id).first()
        if not org:
            return Response({"detail": "Organization not found"}, status=404)
        org.delete()
        return Response({"ok": True})