from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from superadmin_app.models import UserSession

class CookieOrHeaderJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):

        print("\n========== JWT AUTH START ==========")
        print("PATH =", request.path)

        # Skip authentication for public endpoints
        public_paths = [
            "/api/login/",
            "/api/token-refresh/",
            "/api/list-categories/",
            "/api/forgot-password/",
            "/api/reset-password/",
            "/api/verify-otp/",
            "/api/forgot-password/resend-otp/",
        ]

        if request.path in public_paths:
            print("PUBLIC ENDPOINT - AUTH SKIPPED")
            print("========== JWT AUTH END ==========\n")
            return None

        # Authorization Header
        header = self.get_header(request)

        if header:

            print("AUTHORIZATION HEADER FOUND")

            try:

                raw_token = self.get_raw_token(header)

                if raw_token:

                    validated_token = self.get_validated_token(raw_token)

                    print("HEADER TOKEN VALID")

                    user = self.get_user(validated_token)

                    print("AUTHENTICATED USER =", user)

                    print("========== JWT AUTH END ==========\n")

                    return (user, validated_token)

            except (InvalidToken, TokenError, Exception) as e:

                print("HEADER TOKEN ERROR =", str(e))

        # Cookie Authentication
        cookie_token = request.COOKIES.get("access_token")

        print("COOKIE TOKEN FOUND =", bool(cookie_token))

        if cookie_token:

            try:

                validated_token = self.get_validated_token(cookie_token)

                print("COOKIE TOKEN VALID")

                user = self.get_user(validated_token)

                print("AUTHENTICATED USER =", user)

                print("========== JWT AUTH END ==========\n")

                return (user, validated_token)

            except (InvalidToken, TokenError, Exception) as e:

                print("COOKIE TOKEN ERROR =", str(e))
                print("CONTINUING AS ANONYMOUS USER")

                return None

        print("NO TOKEN FOUND")
        print("========== JWT AUTH END ==========\n")

        return None

#     
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from rest_framework.exceptions import AuthenticationFailed
# from django.utils import timezone

# from superadmin_app.models import UserSession

# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import (
#     InvalidToken,
#     TokenError
# )
# from rest_framework.exceptions import AuthenticationFailed
# from django.utils import timezone

# from superadmin_app.models import UserSession


# class CookieOrHeaderJWTAuthentication(
#     JWTAuthentication
# ):

#     def validate_session(
#         self,
#         user,
#         validated_token
#     ):

#         token_jti = validated_token.get(
#             "jti"
#         )

#         if not token_jti:

#             raise AuthenticationFailed(
#                 "Invalid token."
#             )

#         current_version = validated_token.get(
#             "token_version",
#             1
#         )

#         if (
#             current_version
#             != user.token_version
#         ):

#             raise AuthenticationFailed(
#                 "Session invalidated."
#             )

#         session = UserSession.objects.filter(
#             user=user,
#             session_id=token_jti,
#             is_active=True
#         ).first()

#         if not session:

#             raise AuthenticationFailed(
#                 "Session expired or signed out."
#             )

#         if (
#             session.expires_at
#             and
#             session.expires_at < timezone.now()
#         ):

#             session.is_active = False

#             session.save(
#                 update_fields=[
#                     "is_active"
#                 ]
#             )

#             raise AuthenticationFailed(
#                 "Session expired."
#             )

#         session.last_activity = (
#             timezone.now()
#         )

#         session.save(
#             update_fields=[
#                 "last_activity"
#             ]
#         )

#     def authenticate(
#         self,
#         request
#     ):

#         public_paths = [

#             "/api/login/",
#             "/api/token-refresh/",
#             "/api/list-categories/",
#             "/api/forgot-password/",
#             "/api/reset-password/",
#             "/api/verify-otp/",
#             "/api/forgot-password/resend-otp/",
#         ]

#         if request.path in public_paths:
#             return None

#         # ==========================
#         # AUTHORIZATION HEADER
#         # ==========================

#         header = self.get_header(
#             request
#         )

#         if header:

#             try:

#                 raw_token = (
#                     self.get_raw_token(
#                         header
#                     )
#                 )

#                 if raw_token:

#                     validated_token = (
#                         self.get_validated_token(
#                             raw_token
#                         )
#                     )

#                     user = self.get_user(
#                         validated_token
#                     )

#                     self.validate_session(
#                         user,
#                         validated_token
#                     )

#                     return (
#                         user,
#                         validated_token
#                     )

#             except (
#                 InvalidToken,
#                 TokenError,
#                 AuthenticationFailed
#             ):
#                 pass

#         # ==========================
#         # COOKIE TOKEN
#         # ==========================

#         cookie_token = (
#             request.COOKIES.get(
#                 "access_token"
#             )
#         )

#         if cookie_token:

#             try:

#                 validated_token = (
#                     self.get_validated_token(
#                         cookie_token
#                     )
#                 )

#                 user = self.get_user(
#                     validated_token
#                 )

#                 self.validate_session(
#                     user,
#                     validated_token
#                 )

#                 return (
#                     user,
#                     validated_token
#                 )

#             except (
#                 InvalidToken,
#                 TokenError,
#                 AuthenticationFailed
#             ):
#                 pass

#         return None
    
    
# class SessionJWTAuthentication(JWTAuthentication):

#     def authenticate(self, request):

#         result = super().authenticate(request)

#         if result is None:
#             return None

#         user, validated_token = result

#         token_jti = validated_token.get("jti")

#         if not token_jti:
#             raise AuthenticationFailed(
#                 "Invalid token."
#             )

#         current_version = validated_token.get(
#             "token_version",
#             1
#         )

#         if current_version != user.token_version:
#             raise AuthenticationFailed(
#                 "Session invalidated."
#             )

#         session = UserSession.objects.filter(
#             user=user,
#             session_id=token_jti,
#             is_active=True
#         ).first()

#         if not session:
#             raise AuthenticationFailed(
#                 "Session expired or signed out."
#             )

#         if (
#             session.expires_at and
#             session.expires_at < timezone.now()
#         ):

#             session.is_active = False

#             session.save(
#                 update_fields=["is_active"]
#             )

#             raise AuthenticationFailed(
#                 "Session expired."
#             )

#         session.last_activity = timezone.now()

#         session.save(
#             update_fields=["last_activity"]
#         )

#         return (
#             user,
#             validated_token
#         )
    
