from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.permissions import AllowAny, IsAuthenticated


from apps.biometrik.embedding import extract_embedding

from apps.common.models import *

class GetBiometricStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,id):
        user=Users.objects.get(id=id)
        has_face = BiometricFace.objects.filter(user=user).exists()
        has_fingerprint = BiometricFingerprint.objects.filter(user=user).exists()
        print(user,has_fingerprint,has_face)
    
        return  Response({
            "has_face": has_face,
            "has_fingerprint": has_fingerprint
            })


class BiometricFace_(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,id):
        org = request.session.get("current_org_id")
        user= Users.objects.filter(organization=org,id=id).first()
        

        if not user :
            return Response({"error":"Organization have not this user"})
        paimage = request.FILES.get("image")

        embedding = extract_embedding(paimage)

        if hasattr(user,'face') :
            face =BiometricFace.objects.filter(user=user)
            face.delete()

        
        face=BiometricFace.objects.create(user=user)
        face.set_embedding(embedding)
        face.save()

        print(face.get_embedding())

        print(embedding)

        return Response({"seccess":True})
    
    def delete(self,request,id):
        org = request.session.get("current_org_id")
        user= Users.objects.filter(organization=org,id=id).first()
        print(org,user)
        if not user :
            return Response({"error":"Organization have not this user"})

        face =  BiometricFace.objects.filter(user=user)
        print(face)
        face.delete()

        return Response({"success":True})
    

class BiometricFingerprint_(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,id):
        org = request.session.get("current_org_id")
        user= Users.objects.filter(organization=org,id=id).first()
        

        if not user :
            return Response({"error":"Organization have not this user"})
        


import uuid
from django.core.cache import cache

class FingerprintSessionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            user = Users.objects.get(id=id)
        except Users.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        session_token = str(uuid.uuid4())
        # Cache da 5 daqiqa saqlash
        cache.set(f"finger_session_{session_token}", {
            "user_id": user.id,
            "status": "pending"
        }, timeout=300)

        return Response({"session_token": session_token})


class FingerprintSessionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, token):
        data = cache.get(f"finger_session_{token}")
        if not data:
            return Response({"status": "expired"})
        return Response({"status": data["status"]})


class FingerprintSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        data = cache.get(f"finger_session_{token}")
        if not data:
            return Response({"detail": "Session expired"}, status=400)

        embedding = request.data.get("embedding")
        if not embedding:
            return Response({"detail": "embedding required"}, status=400)

        user = Users.objects.get(id=data["user_id"])
        # ModelIngizga qarab o'zgartiring
        BiometricFingerprint.objects.update_or_create(
            user=user,
            defaults={"embedding": embedding}
        )

        data["status"] = "completed"
        cache.set(f"finger_session_{token}", data, timeout=300)

        return Response({"status": "ok"})