from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
import pyotp
# from .utils import decrypt_request_payload
from rest_framework_simplejwt.exceptions import TokenError


class TokenRefreshAPIView(APIView):


    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({
                "status": False,
                "message": "Refresh token is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)

            # Get user from token
            user_id = refresh.payload.get("user_id")

            user = Profiles.objects.filter(id=user_id).first()

            if not user:
                return Response({
                    "status": False,
                    "message": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)

            access_token = refresh.access_token

            # Add custom claims to access token
            access_token["profile_id"] = user.id
            access_token["role"] = user.role
            access_token["email"] = user.email
            access_token["usersid"] = user.user_id
            access_token["category"] = (
                user.category.name if user.category else None
            )

            return Response({
                "status": True,
                "message": "Token refreshed successfully",
                "tokens": {
                    "access": str(access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                "status": False,
                "message": "Token is invalid or expired"
            }, status=status.HTTP_401_UNAUTHORIZED)


# Create your views here.

class LoginAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        # serializer = LoginSerializer(data=request.data)
        print("REQUEST DATA:", request.data)

        serializer = LoginSerializer(data=request.data)

        print("SERIALIZER VALID:", serializer.is_valid())
        print("SERIALIZER ERRORS:", serializer.errors)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get("user_id")

        password = serializer.validated_data.get("password")

        category_id = serializer.validated_data.get("category_id")

        user = Profiles.objects.filter(user_id=user_id).first()

        if not user:
            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({
                "status": False,
                "message": "Invalid password"
            }, status=status.HTTP_401_UNAUTHORIZED)

        # =========================================
        # ASSIGN CATEGORY DURING LOGIN
        # =========================================
        if category_id:

            try:
                category = Category.objects.get(id=category_id)

                user.category = category
                user.save()

            except Category.DoesNotExist:

                return Response({
                    "status": False,
                    "message": "Invalid category_id"
                }, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        refresh["profile_id"] = user.id
        refresh["role"] = user.role
        refresh["email"] = user.email
        refresh["usersid"] = user.user_id
        refresh["category"] = user.category.name if user.category else None

        return Response({
            "status": True,
            "message": "Login successful",

            "user": {
                "id": user.id,
                "usersid": user.user_id,
                "role": user.role,
                "name": user.fullname,
                "category": user.category.name if user.category else None,
            },

            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }

        }, status=status.HTTP_200_OK)
    

# list category
class ListCategoryAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        categories = Category.objects.all()

        data = []

        for category in categories:
            data.append({
                "id": category.id,
                "name": category.name,
                "description": category.description
            })

        return Response({
            "status": True,
            "categories": data
        }, status=status.HTTP_200_OK)



# forgot password view
class ForgotPasswordAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")

        if not email:
            return Response({
                "status": False,
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = Profiles.objects.filter(
            email=email
        ).first()

        if not user:
            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        OTPVerification.objects.filter(
            user=user,
            purpose='forgot_password',
            is_used=False
        ).update(
            is_used=True
        )

        secret = pyotp.random_base32()

        totp = pyotp.TOTP(
            secret,
            interval=300
        )

        otp = totp.now()

        OTPVerification.objects.create(
            user=user,
            secret=secret,
            otp=otp,
            purpose='forgot_password',
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is {otp}. It will expire in 5 minutes.",
            from_email=None,
            recipient_list=[email],
            fail_silently=False
        )

        return Response({
            "status": True,
            "message": "OTP sent successfully"
        })
    

# verify otp 
class VerifyOTPAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email:
            return Response({
                "status": False,
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not otp:
            return Response({
                "status": False,
                "message": "OTP is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = Profiles.objects.filter(email=email).first()

        if not user:
            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        otp_record = OTPVerification.objects.filter(
            user=user,
            purpose='forgot_password',
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record:
            return Response({
                "status": False,
                "message": "OTP not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check expiry
        if timezone.now() > otp_record.expires_at:
            return Response({
                "status": False,
                "message": "OTP expired"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check max attempts
        if otp_record.attempts >= otp_record.max_attempts:
            return Response({
                "status": False,
                "message": "Maximum OTP attempts exceeded"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Increase attempts
        otp_record.attempts += 1
        otp_record.save(update_fields=["attempts"])

        # Verify OTP using pyotp
        totp = pyotp.TOTP(
            otp_record.secret,
            interval=300
        )

        if not totp.verify(str(otp)):
            return Response({
                "status": False,
                "message": "Invalid OTP",
                "remaining_attempts":
                    otp_record.max_attempts - otp_record.attempts
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.used_at = timezone.now()
        otp_record.save(update_fields=["is_used", "used_at"])

        return Response({
            "status": True,
            "message": "OTP verified successfully"
        }, status=status.HTTP_200_OK)
    

    # reset pasword section 
class ResetPasswordAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not email:
            return Response({
                "status": False,
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({
                "status": False,
                "message": "New password is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not confirm_password:
            return Response({
                "status": False,
                "message": "Confirm password is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({
                "status": False,
                "message": "Passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = Profiles.objects.filter(email=email).first()

        if not user:
            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check whether OTP was verified
        verified_otp = OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password",
            is_used=True
        ).order_by("-used_at").first()

        if not verified_otp:
            return Response({
                "status": False,
                "message": "OTP verification required before resetting password"
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        # Optional: delete or invalidate verified OTP records
        OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password"
        ).delete()

        return Response({
            "status": True,
            "message": "Password reset successfully"
        }, status=status.HTTP_200_OK)

#resend otp 
class ResendForgotPasswordOTPAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "status": False,
                    "message": "Email is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Profiles.objects.get(email=email)

        except Profiles.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Email not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password",
            is_used=False
        ).update(is_used=True)

        # Generate Secret
        secret = pyotp.random_base32()

        # Generate OTP valid for 1 minute
        totp = pyotp.TOTP(
            secret,
            interval=300
        )

        otp = totp.now()

        OTPVerification.objects.create(
            user=user,
            otp=otp,
            secret=secret,
            purpose="forgot_password",
            is_used=False,
            attempts=0,
            expires_at=timezone.now() + timedelta(minutes=1)
        )

        send_mail(
            subject="OTP to Reset Your Password",
            message=f"Your OTP is {otp}. It is valid for 1 minute.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        return Response(
            {
                "status": True,
                "message": "OTP resent successfully",
            },
            status=status.HTTP_200_OK
        )
    

# logout api 
class LogoutAPIView(APIView):
    """
    API to logout user by blacklisting the refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({
                "status": False,
                "message": "Refresh token is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "status": True,
                "message": "Logout successful"
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                "status": False,
                "message": "Invalid or expired refresh token"
            }, status=status.HTTP_400_BAD_REQUEST)