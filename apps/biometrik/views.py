from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.permissions import AllowAny, IsAuthenticated


from apps.biometrik.embedding import extract_embedding

from apps.common.models import *

class GetBiometricStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,id):
        user=Users.objects.get(id=id)
        has_face = hasattr(user, "face"),
        has_fingerprint = hasattr(user, "fingerprint")
        print(user,has_fingerprint,has_face[0])
    
        return  Response({
            "has_face": has_face[0],
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
        


class Fingerprint(APIView):
    permission_classes = [IsAuthenticated]

    def 

