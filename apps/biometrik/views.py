import base64, os, tempfile, numpy as np
from django.shortcuts import render
from rest_framework.views import APIView, Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

from apps.biometrik.embedding import extract_embedding

from apps.common.models import *
from apps.biometrik.models import *

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

        face = BiometricFace.objects.filter(user=user).order_by('created_at').first()

        if face:
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
    


class FingerprintPhoneStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("user_id")
        user = Users.objects.get(id=user_id)
        FingerprintSession.cleanup_expired()

        session = FingerprintSession.objects.create(
            user=user
        )

        return Response({
            "session_id": str(session.session_id),
            "expires_in": 120,
            "status": session.status
        })



class FingerprintPhoneSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = request.data.get("session_id")
        raw_id = request.data.get("rawId")
        client_data = request.data.get("clientDataJSON")
        attestation = request.data.get("attestationObject")

        session = FingerprintSession.objects.get(session_id=session_id)

        if session.status != "pending":
            return Response(
                {"error": "Session invalid"},
                status=400
            )

        if session.expires_at < timezone.now():
            session.status = "expired"
            session.save()
            return Response(
                {"error": "Session expired"},
                status=400
            )

        if not raw_id or not client_data or not attestation:
            return Response(
                {"error": "Credential incomplete"},
                status=400
            )

        combined = f"{raw_id}|{client_data}|{attestation}"

        fingerprint = BiometricFingerprint.objects.create(
            user=session.user,
            source="phone"
        )

        fingerprint.set_embedding(combined.encode())
        fingerprint.save()

        session.status = "completed"
        session.save()

        return Response({
            "status": "ok",
            "message": "Fingerprint saved"
        })
    
    

class FingerprintPhoneStatusView(APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def get(self, request, session_id):
        session = FingerprintSession.objects.get(session_id=session_id)
        print(session.status)

        if session.expires_at < timezone.now():
            session.status = "expired"
            session.save()

        return Response({
            "status": session.status
        })
    
    


class BiometricFingerprintListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        user =  Users.objects.get(id=id)
        fingerprints = BiometricFingerprint.objects.filter(
            user=user
        )

        data = []

        for fp in fingerprints:
            data.append({
                "id": fp.id,
                "source": fp.source,
                "created_at": fp.created_at
            })

        return Response(data)
    
    def delete(self,request,user_id,id):
        print("sihladi")
        user =  Users.objects.get(id=user_id)
        fingerprints = BiometricFingerprint.objects.filter(
            user=user,id=id
        )

        fingerprints.delete()
        
        return Response({'succes':True})

    

class MobileFingerprintView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, session_id):
        return render(
            request,
            "mobile_fingerprint.html",
            {"session_id": session_id}
        )





class PhoneFaceChecker(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = request.data.get("session_id")
        print(session_id)

        image_b64 = request.data.get("image")

        if not session_id or not image_b64:
            return Response(
                {"detail": "session_id va image majburiy"},
                status=400
            )

        # 1. Session
        try:
            session = FingerprintSession.objects.get(session_id=session_id)
        except FingerprintSession.DoesNotExist:
            return Response(
                {"detail": "Session topilmadi"},
                status=404
            )

        # 2. Userning barcha face embeddinglari
        face_records = BiometricFace.objects.filter(user=session.user)

        if not face_records.exists():
            return Response(
                {"status": "not_found"},
                status=200
            )

        # 3. Base64 decode
        try:
            img_bytes = base64.b64decode(image_b64)
        except Exception as e:
            return Response(
                {"detail": "Base64 decode xato: " + str(e)},
                status=400
            )

        # 4. Temp file orqali embedding olish
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            incoming_bytes = extract_embedding(tmp_path)

        except Exception as e:
            return Response(
                {"detail": "Rasmdan yuz topilmadi: " + str(e)},
                status=400
            )

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # 5. Incoming embedding
        incoming_embedding = np.frombuffer(
            incoming_bytes,
            dtype=np.float64
        )

        # 6. Eng yaxshi similarity topish
        best_similarity = 0

        for face in face_records:
            saved_bytes = face.get_embedding()

            if not saved_bytes:
                continue

            saved_embedding = np.frombuffer(
                saved_bytes,
                dtype=np.float64
            )

            similarity = _cosine_similarity(
                saved_embedding,
                incoming_embedding
            )

            if similarity > best_similarity:
                best_similarity = similarity

        # 7. Threshold
        THRESHOLD = 0.65

        print(best_similarity)
        new_face = BiometricFace(user=session.user)
        # 8. Verify
        if best_similarity >= THRESHOLD:
            
            if best_similarity >= 0.7 and best_similarity<=80:
                if 10 >len( BiometricFace.objects.filter(user=session.user)):
                    new_face.set_embedding(incoming_bytes)
                    new_face.save()
                
            return Response({
                "status": "verified",
                "similarity": round(float(best_similarity), 4)
            })

        return Response({
            "status": "mismatch",
            "similarity": round(float(best_similarity), 4)
        })
    


def _cosine_similarity(a, b):
    a = a / (np.linalg.norm(a) + 1e-10)
    b = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a, b))