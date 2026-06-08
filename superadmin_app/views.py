from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import request, status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db import transaction 
import secrets
import string
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from superadmin_app import pagination
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font


from superadmin_app.utils.security_utils import (
    get_client_ip,
    get_browser,
    get_device,
    get_location,
    )


# Create your views here.

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

            user_id = refresh.payload.get("user_id")

            user = Profiles.objects.filter(
                id=user_id
            ).first()

            if not user:

                return Response({
                    "status": False,
                    "message": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # =====================================
            # TOKEN VERSION VALIDATION
            # =====================================

            token_version = refresh.payload.get(
                "token_version",
                0
            )

            if token_version != user.token_version:

                return Response({
                    "status": False,
                    "message":
                    "Session expired. Please login again."
                }, status=status.HTTP_401_UNAUTHORIZED)

            access_token = refresh.access_token

            # =====================================
            # CUSTOM CLAIMS
            # =====================================

            access_token["profile_id"] = user.id
            access_token["role"] = user.role
            access_token["email"] = user.email
            access_token["usersid"] = user.user_id
            access_token["category"] = (
                user.category.name
                if user.category
                else None
            )

            access_token["token_version"] = (
                user.token_version
            )

            return Response({

                "status": True,
                "message":
                "Token refreshed successfully",

                "tokens": {
                    "access": str(access_token),
                    "refresh": str(refresh)
                }

            }, status=status.HTTP_200_OK)

        except TokenError:

            return Response({
                "status": False,
                "message":
                "Token is invalid or expired"
            }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:

            print(
                "TOKEN REFRESH ERROR =",
                str(e)
            )

            return Response({
                "status": False,
                "message":
                "Unable to refresh token."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        browser = get_browser(user_agent)
        device_name = get_device(user_agent)
        location = get_location(ip_address)

        if not user:

            try:

                LoginHistory.objects.create(
                    login_time=timezone.now(),
                    login_status='FAILED',
                    ip_address=ip_address,
                    browser=browser,
                    device_name=device_name,
                    location=location,
                    raw_user_agent=user_agent
                )

            except Exception as e:

                print('FAILED LOGIN HISTORY ERROR =', str(e))

            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):

            try:

                LoginHistory.objects.create(
                    user=user,
                    login_time=timezone.now(),
                    login_status='FAILED',
                    ip_address=ip_address,
                    browser=browser,
                    device_name=device_name,
                    location=location,
                    raw_user_agent=user_agent
                )

            except Exception as e:

                print('FAILED LOGIN HISTORY ERROR =', str(e))

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
        refresh['token_version'] = user.token_version

        access_token = refresh.access_token
        session_jti = access_token['jti']

        try:

            print("ABOUT TO CREATE LOGIN HISTORY")

            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = get_client_ip(request)
            browser = get_browser(user_agent)
            device_name = get_device(user_agent)
            location = get_location(ip_address)

            LoginHistory.objects.filter(
                user=user,
                logout_time__isnull=True
            ).update(
                logout_time=timezone.now(),
                login_status='LOGOUT'
            )

            LoginHistory.objects.create(
                user=user,
                login_time=timezone.now(),
                login_status='SUCCESS',
                ip_address=ip_address,
                device_name=device_name,
                browser=browser,
                location=location,
                raw_user_agent=user_agent,
                )         
                

            print("LOGIN HISTORY CREATED")

        except Exception as e:

            print(
                "LOGIN HISTORY ERROR =",
                str(e)
            )

        try:

            print("ABOUT TO CREATE SESSION")

            

            UserSession.objects.filter(
                user=user,
            
                is_active=True
            ).update(is_active=False)

            UserSession.objects.create(
                user=user,
                session_id=session_jti,
                token_version=user.token_version,
                device_name=device_name,
                browser=browser,
                ip_address=ip_address,
                location=location,
                is_active=True,
                expires_at=(timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])
            )

            

            print('ACTIVE SESSION CREATED FOR =', user.user_id)
            print('EXPIRES AT =',timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])

            print("SESSION CREATED")

        except Exception as e:

            print(
                "SESSION ERROR =",
                str(e)
            )

        refresh["profile_id"] = user.id
        refresh["role"] = user.role
        refresh["email"] = user.email
        refresh["usersid"] = user.user_id
        refresh["category"] = user.category.name if user.category else None
        refresh["token_version"] = user.token_version
        return Response({
            "status": True,
            "message": "Login successful",

            "user": {
                "id": user.id,
                "usersid": user.user_id,
                "role": user.role,
                "name": user.fullname or user.user_id,
                "category": user.category.name if user.category else None,
            },

            "tokens": {
                "access": str(access_token),
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



 # save the category such as school or college 

# class AssignCategoryAPIView(APIView):

    #     permission_classes = [IsAuthenticated]

    #     def post(self, request):

    #         category_id = request.data.get("category_id")

    #         try:

    #             category = Category.objects.get(id=category_id)

    #         except Category.DoesNotExist:

    #             return Response({
    #                 "status": False,
    #                 "message": "Category not found"
    #             })

    #         user = request.user

    #         user.category = category
    #         user.save()

    #         return Response({
    #             "status": True,
    #             "message": "Category assigned successfully"
    #         })


# =================================== 
# Profile Settings
# ===================================


class ProfileSettingsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            serializer = ProfileSettingsSerializer(
                request.user
            )

            return Response({
                "status": True,
                "message": "Profile fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:

            print("PROFILE FETCH ERROR =", str(e))

            return Response({
                "status": False,
                "message": "Unable to fetch profile details."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ProfileSettingsUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):

        try:

            user = request.user

            serializer = ProfileSettingsUpdateSerializer(
                user,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():

                return Response({
                    "status": False,
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():

                serializer.save()

            print(
                f"PROFILE UPDATED: {user.user_id}"
            )

            return Response({
                "status": True,
                "message": "Profile updated successfully.",
                "data": ProfileSettingsSerializer(user).data
            }, status=status.HTTP_200_OK)

        except Exception as e:

            print("PROFILE UPDATE ERROR =", str(e))

            return Response({
                "status": False,
                "message": "Unable to update profile.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request):

        return self.put(request)
    
class ChangePasswordAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        current_password = (
            serializer.validated_data[
                "current_password"
            ]
        )

        if not request.user.check_password(
            current_password
        ):

            return Response({
                "status": False,
                "message":
                "Current password is incorrect."
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(
            serializer.validated_data[
                "new_password"
            ]
        )

        request.user.save()

        print(
            f"PASSWORD CHANGED: {request.user.user_id}"
        )
        
        return Response({
            "status": True,
            "message":
            "Password changed successfully."
        }, status=status.HTTP_200_OK)
    
class LogoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            refresh_token = request.data.get('refresh')

            if refresh_token:
                try:
                    RefreshToken(refresh_token).blacklist()
                except Exception:
                    pass

            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = get_client_ip(request)
            browser = get_browser(user_agent)
            device_name = get_device(user_agent)
            location = get_location(ip_address)

            latest_login = LoginHistory.objects.filter(
            user=request.user,
            logout_time__isnull=True
            ).order_by('-created_at').first()

            if latest_login and not latest_login.logout_time:
                latest_login.logout_time = timezone.now()
                latest_login.login_status = 'LOGOUT'
                latest_login.save(update_fields=['logout_time', 'login_status'])

            header = request.META.get('HTTP_AUTHORIZATION', '')
            current_token = header.replace('Bearer ', '').strip()

            try:
                from rest_framework_simplejwt.tokens import AccessToken
                current_jti = AccessToken(current_token)['jti']

                UserSession.objects.filter(
                    user=request.user,
                    session_id=current_jti,
                    is_active=True
                ).update(is_active=False)
            
            except Exception :

                UserSession.objects.filter(
                    user=request.user,
                    is_active=True
                ).update(is_active=False)

            return Response({
                'status': True,
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)

        except Exception as e:

            print('LOGOUT ERROR =', str(e))

            return Response({
                'status': False,
                'message': 'Unable to logout.'
            }, status=500)

    


# =========================================
# SECURITY SETTINGS
# ========================================= 

class SecurityDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            if request.user.role in [
                'SuperAdmin',
                'Administration staff'
            ]:

                data = {
                    "total_logins": LoginHistory.objects.exclude(
                        login_status='FAILED'
                    ).count(),

                    "total_failed_logins": LoginHistory.objects.filter(
                        login_status='FAILED'
                    ).count(),

                    "active_sessions": UserSession.objects.filter(
                        is_active=True,
                        expires_at__gt=timezone.now()
                    ).count(),

                    "password_resets": PasswordResetAudit.objects.count()
                }

            else:

                data = {
                    "total_logins": LoginHistory.objects.filter(
                        user=request.user
                    ).exclude(
                        login_status='FAILED'
                    ).count(),

                    "total_failed_logins": LoginHistory.objects.filter(
                        user=request.user,
                        login_status='FAILED'
                    ).count(),

                    "active_sessions": UserSession.objects.filter(
                        user=request.user,
                        is_active=True,
                        expires_at__gt=timezone.now()
                    ).count(),

                    "password_resets": PasswordResetAudit.objects.filter(
                        reset_by=request.user
                    ).count()
                }

            serializer = SecurityDashboardSerializer(
                instance=data
            )

            return Response({
                "status": True,
                "message":
                "Security dashboard fetched successfully.",
                "data": serializer.data
            })
        
        

        except Exception as e:

            print(
                "SECURITY DASHBOARD ERROR =",
                str(e)
            )

            return Response({
                "status": False,
                "message":
                "Unable to fetch security dashboard."
            }, status=500)
        

class LoginHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            if request.user.role in ['SuperAdmin', 'Administration staff']:

                queryset = (
                    LoginHistory.objects
                    .select_related('user')
                    .order_by('-created_at')
                )

            else:

                queryset = (
                    LoginHistory.objects
                    .select_related('user')
                    .filter(user=request.user)
                    .order_by('-created_at')
                )

            # ==========================
            # FILTERS
            # ==========================

            name = request.GET.get('name')
            login_date = request.GET.get('login_date')

            if name:
                queryset = queryset.filter(
                    user__fullname__icontains=name
                )

            if login_date:
                queryset = queryset.filter(
                created_at__date=login_date
                )

            # ==========================
            # PAGINATION
            # ==========================

            paginator = pagination.LoginHistoryPagination()

            page = paginator.paginate_queryset(
                queryset,
                request
            )

            serializer = LoginHistorySerializer(
                page,
                many=True
            )

            return paginator.get_paginated_response(
                serializer.data
            )

        except Exception as e:

            print(
                "LOGIN HISTORY ERROR =",
                str(e)
            )

            return Response({
                "status": False,
                "message":
                "Unable to fetch login history."
            }, status=500)
        
class ExportLoginHistoryExcelAPIView(APIView):

    permission_classes = [IsAuthenticated]

    

    def get(self, request):

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Login History'

        headers = [
            'User ID',
            'Full Name',
            'Login Time',
            'Logout Time',
            'Status',
            'IP Address',
            'Browser',
            'Device',
            'Location'
        ]

        for col_num, header in enumerate(headers, 1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)

        if request.user.role in ['SuperAdmin', 'Administration staff']:

            queryset = LoginHistory.objects.all().order_by('-created_at')

        else:

            queryset = LoginHistory.objects.filter(
                user=request.user
            ).order_by('-created_at')

        row_num = 2

        for item in queryset:

            login_time = (
                timezone.localtime(item.login_time).strftime(
                    '%d-%m-%Y %I:%M:%S %p'
                )
                if item.login_time else ''
            )

            logout_time = (
                timezone.localtime(item.logout_time).strftime(
                    '%d-%m-%Y %I:%M:%S %p'
                )
                if item.logout_time else ''
            )

            sheet.cell(row=row_num, column=1).value = (
                item.user.user_id
                if item.user
                else 'Unknown User'
            )

            sheet.cell(row=row_num, column=2).value = (
                item.user.fullname
                if item.user
                else '-'
            )
            sheet.cell(row=row_num, column=3).value = login_time
            sheet.cell(row=row_num, column=4).value = logout_time
            sheet.cell(row=row_num, column=5).value = item.login_status
            sheet.cell(row=row_num, column=6).value = item.ip_address
            sheet.cell(row=row_num, column=7).value = item.browser
            sheet.cell(row=row_num, column=8).value = item.device_name
            sheet.cell(row=row_num, column=9).value = item.location

            row_num += 1

        for column in sheet.columns:

            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if cell.value:
                        max_length = max(
                            max_length,
                            len(str(cell.value))
                        )
                except Exception:
                    pass

            sheet.column_dimensions[column_letter].width = max_length + 5

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = (
            'attachment; filename="login_history.xlsx"'
        )

        workbook.save(response)

        return response
    

class ActiveSessionAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            expired_sessions = UserSession.objects.filter(
                is_active=True,
                expires_at__lte=timezone.now()
            ).select_related('user')

            for session in expired_sessions:

                session.is_active = False
                session.save(update_fields=['is_active'])

                latest_login = LoginHistory.objects.filter(
                    user=session.user,
                    logout_time__isnull=True
                ).order_by('-created_at').first()

                if latest_login:

                    latest_login.logout_time = session.expires_at
                    latest_login.login_status = 'LOGOUT'

                    latest_login.save(
                        update_fields=[
                            'logout_time',
                            'login_status'
                        ]
                    )

            if request.user.role in [
                'SuperAdmin',
                'Administration staff'
            ]:

                queryset = (
                    UserSession.objects
                    .select_related('user')
                    .filter(
                        is_active=True,
                        expires_at__gt=timezone.now()
                    )
                    .order_by('-created_at')
                )

            else:

                queryset = (
                    UserSession.objects
                    .select_related('user')
                    .filter(
                        user=request.user,
                        is_active=True,
                        expires_at__gt=timezone.now()
                    )
                    .order_by('-created_at')
                )

            serializer = ActiveSessionSerializer(
                queryset,
                many=True
            )

            return Response({
                'status': True,
                'count': len(serializer.data),
                'data': serializer.data
            })

        except Exception as e:

            print(
                'ACTIVE SESSION ERROR =',
                str(e)
            )

            return Response({
                'status': False,
                'message':
                'Unable to fetch active sessions.'
            }, status=500)
        


class SessionSignOutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        if not request.data.get('session_id'):
            return Response({
                'status': False,
                'message': 'session_id is required.'
            }, status=400)

        session_id = request.data.get('session_id')

        session = UserSession.objects.filter(
            id=session_id,
            is_active=True
        ).select_related('user').first()

        if not session:
            return Response({
                'status': False,
                'message': 'Session not found.'
            }, status=404)

        if request.user.role not in [
            'SuperAdmin',
            'Administration staff'
        ] and session.user != request.user:

            return Response({
                'status': False,
                'message': 'Permission denied.'
            }, status=403)

        session.is_active = False
        session.save(update_fields=['is_active'])

        latest_login = LoginHistory.objects.filter(
            user=session.user,
            logout_time__isnull=True
        ).order_by('-created_at').first()

        if latest_login:
            latest_login.logout_time = timezone.now()
            latest_login.login_status = 'LOGOUT'
            latest_login.save(
                update_fields=[
                    'logout_time',
                    'login_status'
                ]
            )

        return Response({
            'status': True,
            'message': 'Session signed out successfully.',
            'affected_user': session.user.user_id
        })
    
class LogoutAllDevicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        request.user.token_version += 1
        request.user.save(update_fields=['token_version'])

        count = UserSession.objects.filter(
        user=request.user,
        is_active=True
        ).update(
        is_active=False,
        token_version=request.user.token_version
        )

        open_logins = LoginHistory.objects.filter(
            user=request.user,
            logout_time__isnull=True
        )

        for login in open_logins:

            login.logout_time = timezone.now()
            login.login_status = 'LOGOUT'

            login.save(
                update_fields=[
                    'logout_time',
                    'login_status'
                ]
            )

        return Response({
            'status': True,
            'message': 'All devices logged out successfully.',
            'affected_sessions': count
        })


class ForceLogoutUserAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.role not in [
            'SuperAdmin',
            'Administration staff'
        ]:

            return Response({
                'status': False,
                'message': 'Permission denied.'
            }, status=403)

        target_user_id = request.data.get('user_id')

        target_user = Profiles.objects.filter(
            user_id=target_user_id
        ).first()

        if not target_user:
            return Response({
                'status': False,
                'message': 'User not found.'
            }, status=404)

        target_user.token_version += 1
        target_user.save(update_fields=['token_version'])

        count = UserSession.objects.filter(
        user=target_user,
        is_active=True
        ).update(
        is_active=False,
        token_version=target_user.token_version
        )

        open_logins = LoginHistory.objects.filter(
            user=target_user,
            logout_time__isnull=True
        )

        for login in open_logins:

            login.logout_time = timezone.now()
            login.login_status = 'LOGOUT'

            login.save(
                update_fields=[
                    'logout_time',
                    'login_status'
                ]
            )

        return Response({
            'status': True,
            'message': 'User force logged out successfully.',
            'affected_sessions': count
        })
class ResetPasswordAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            if request.user.role not in ['SuperAdmin', 'Administration staff']:

                return Response({
                    "status": False,
                    "message":
                    "Permission denied."
                }, status=403)

            serializer = (
                PasswordResetSerializer(
                    data=request.data
                )
            )

            if not serializer.is_valid():

                return Response({
                    "status": False,
                    "errors":
                    serializer.errors
                }, status=400)

            user = Profiles.objects.get(
                user_id=
                serializer.validated_data[
                    'user_id'
                ]
            )

            alphabet = (
                string.ascii_letters +
                string.digits +
                "@#$%&!"
            )

            temporary_password = ''.join(
                secrets.choice(alphabet)
                for _ in range(12)
            )

            user.set_password(
                temporary_password
            )

            user.save()

            email_sent = False

            if (
                serializer.validated_data.get(
                    'send_email',
                    True
                )
                and
                user.email
            ):

                try:

                    send_mail(
                        subject=
                        "Password Reset",
                        message=
                        f"Temporary Password: "
                        f"{temporary_password}",
                        from_email=None,
                        recipient_list=[
                            user.email
                        ],
                        fail_silently=False
                    )

                    email_sent = True

                except Exception as mail_error:

                    print(
                        "MAIL ERROR =",
                        str(mail_error)
                    )

            PasswordResetAudit.objects.create(

                target_user=user,

                reset_by=request.user,

                temporary_password_sent=
                email_sent,

                remarks=
                serializer.validated_data.get(
                    'remarks'
                )
            )

            return Response({
                "status": True,
                "message":
                "Password reset successfully.",
                "temporary_password":
                temporary_password
            })

        except Profiles.DoesNotExist:

            return Response({
                "status": False,
                "message":
                "User not found."
            }, status=404)

        except Exception as e:

            print(
                "RESET PASSWORD ERROR =",
                str(e)
            )

            return Response({
                "status": False,
                "message":
                "Unable to reset password."
            }, status=500)
        

class UserListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            if request.user.role not in [
                'SuperAdmin',
                'Administration staff'
            ]:

                return Response({
                    'status': False,
                    'message': 'Permission denied.'
                }, status=403)

            users = Profiles.objects.all().order_by('fullname')

            data = []

            for user in users:

                data.append({
                    'id': user.id,
                    'user_id': user.user_id,
                    'fullname': user.fullname,
                    'role': user.role,
                    'email': user.email,
                    'photo': (
                        request.build_absolute_uri(user.photo.url)
                        if user.photo else None
                    )
                })

            return Response({
                'status': True,
                'count': len(data),
                'data': data
            })

        except Exception as e:

            print(
                'USER LIST ERROR =',
                str(e)
            )

            return Response({
                'status': False,
                'message': 'Unable to fetch users.'
            }, status=500)
        

