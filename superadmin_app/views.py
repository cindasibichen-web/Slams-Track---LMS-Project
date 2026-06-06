import openpyxl
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from administration_app.pagination import ListPagination
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
import pyotp
# from .utils import decrypt_request_payload
from rest_framework_simplejwt.exceptions import TokenError
from collections import defaultdict
from io import BytesIO
from openpyxl.styles import Font
from openpyxl import Workbook
from django.db.models import Count


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
        


#***************************Attendance management views for teachers *******************************
# kpi cards 
class AttendanceManagementKPICardsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date_param = request.query_params.get("date")
        if date_param:
            try:
                selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            selected_date = timezone.now().date()

        # =======================
        # Students
        # =======================

        total_students = Profiles.objects.filter(
            role="Student"
        ).count()

        present_students = StudentAttendance.objects.filter(
            date=selected_date,
            status="Present"
        ).count()

        student_attendance_rate = (
            round((present_students / total_students) * 100, 2)
            if total_students > 0 else 0
        )

        # =======================
        # Teachers
        # =======================

        total_teachers = StaffManagementModel.objects.filter(
            designation="Teacher",
            is_teacher=True
        ).count()

        present_teachers = TeacherstaffAttendance.objects.filter(
            date=selected_date,
            status="Present",
            teacher__is_teacher=True
        ).count()

        absent_teachers = TeacherstaffAttendance.objects.filter(
            date=selected_date,
            status="Absent",
            teacher__is_teacher=True
        ).count()

        teacher_attendance_rate = (
            round((present_teachers / total_teachers) * 100, 2)
            if total_teachers > 0 else 0
        )

        # =======================
        # Staff
        # =======================

        total_staff = StaffManagementModel.objects.filter(
            is_teacher=False
        ).count()

        present_staff = TeacherstaffAttendance.objects.filter(
            date=selected_date,
            status="Present",
            teacher__is_teacher=False
        ).count()

        absent_staff = TeacherstaffAttendance.objects.filter(
            date=selected_date,
            status="Absent",
            teacher__is_teacher=False
        ).count()

        staff_attendance_rate = (
            round((present_staff / total_staff) * 100, 2)
            if total_staff > 0 else 0
        )

        return Response({
            "status": True,
            "message": "Attendance KPI cards data retrieved successfully",
            "data": [
        {
            "title": "Student Attendance Today",
            "present": present_students,
            "total": total_students,
            "count": f"{present_students}/{total_students}",
            "attendance_rate": student_attendance_rate
        },
        {
            "title": "Teachers Attendance Today",
            "present": present_teachers,
            "total": total_teachers,
            "count": f"{present_teachers}/{total_teachers}",
            "attendance_rate": teacher_attendance_rate
        },
        {
            "title": "Staff Attendance Today",
            "present": present_staff,
            "total": total_staff,
            "count": f"{present_staff}/{total_staff}",
            "attendance_rate": staff_attendance_rate
        }
    ]
})


# list teachers attendance based on date
# class TeacherAttendanceListAPIView(APIView):

#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         date = request.query_params.get("date")

#         if not date:
#             return Response({
#                 "status": False,
#                 "message": "Date query parameter is required in YYYY-MM-DD format"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             selected_date = datetime.strptime(date, "%Y-%m-%d").date()
#         except ValueError:
#             return Response({
#                 "status": False,
#                 "message": "Invalid date format. Use YYYY-MM-DD"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         teachers = StaffManagementModel.objects.filter(designation="Teacher",is_teacher=True)

#         attendance_records = TeacherstaffAttendance.objects.filter(
#             date=selected_date
#         )

#         attendance_dict = {
#             attendance.teacher_id: attendance
#             for attendance in attendance_records
#         }

#         data = []

#         for teacher in teachers:

#             attendance = attendance_dict.get(teacher.id)

#             data.append({
#                 "id" : attendance.id if attendance else None,

#                 "profile_id": teacher.id,
#                 "teacher_id": teacher.profiles.user_id,
#                 "teacher_name": teacher.staff_name,
#                 "teacher_department": teacher.department,
                
#                 "date": selected_date,
#                 "status": attendance.status if attendance else "Not Marked",
#                 "remarks": attendance.remarks if attendance else None,
#                 "checked_in_time": attendance.checked_in_time if attendance else None,
#                 "checked_out_time": attendance.checked_out_time if attendance else None,
#             })

#         # Pagination
#         paginator = ListPagination()

#         paginated_data = paginator.paginate_queryset(
#             data,
#             request
#         )

#         return paginator.get_paginated_response({
#             "status": True,
#             "message": "Teacher attendance records retrieved successfully",
#             "attendance": paginated_data
#         }, status=status.HTTP_200_OK)

class TeacherAttendanceListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            selected_date = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)

        teachers = StaffManagementModel.objects.filter(
            designation="Teacher",
            is_teacher=True
        ).select_related("profiles")

        attendance_records = TeacherstaffAttendance.objects.filter(
            date=selected_date
        )

        attendance_dict = {
            attendance.teacher_id: attendance
            for attendance in attendance_records
        }

        # Get levels handled by each teacher
        teacher_level_map = defaultdict(list)

        timetable_data = TeachersTimeTable.objects.select_related(
            "class_assigned"
        ).values(
            "teacher_id",
            "class_assigned__level"
        ).distinct()

        for item in timetable_data:

            level = item.get("class_assigned__level")

            if level and level not in teacher_level_map[item["teacher_id"]]:
                teacher_level_map[item["teacher_id"]].append(level)

        data = []

        for teacher in teachers:

            attendance = attendance_dict.get(teacher.id)

            data.append({
                "id": attendance.id if attendance else None,

                "profile_id": teacher.id,
                "teacher_id": teacher.profiles.user_id if teacher.profiles else None,
                "teacher_name": teacher.staff_name,
                "teacher_department": teacher.department,

                # Added level
                "level": teacher_level_map.get(teacher.id, []),

                "date": selected_date,
                "status": attendance.status if attendance else "Not Marked",
                "remarks": attendance.remarks if attendance else None,
                "checked_in_time": attendance.checked_in_time if attendance else None,
                "checked_out_time": attendance.checked_out_time if attendance else None,
            })

        paginator = ListPagination()

        paginated_data = paginator.paginate_queryset(
            data,
            request
        )

        return paginator.get_paginated_response({
            "status": True,
            "message": "Teacher attendance records retrieved successfully",
            "attendance": paginated_data
        })



# mark attendance for teachers 
# class MarkTeachersAttendance(APIView):

#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         serializer = MarkTeachersAttendanceSerializer(data=request.data)

#         if not serializer.is_valid():
#             return Response({
#                 "status": False,
#                 "errors": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#         teacher_id = serializer.validated_data.get("teacher_id")
#         date = serializer.validated_data.get("date")
#         status_attendance = serializer.validated_data.get("status")
#         remarks = serializer.validated_data.get("remarks", None)

#         checked_in_time = serializer.validated_data.get("checked_in_time", None)
#         checked_out_time = serializer.validated_data.get("checked_out_time", None)

#         teacher = StaffManagementModel.objects.filter(
#             id=teacher_id,
#             designation="Teacher",
#             is_teacher=True
#         ).first()

#         if not teacher:
#             return Response({
#                 "status": False,
#                 "message": "Teacher not found"
#             }, status=status.HTTP_404_NOT_FOUND)

#         attendance_record, created = TeacherstaffAttendance.objects.get_or_create(
#             teacher=teacher,
#             date=date
#         )

#         # Always update attendance status
#         attendance_record.status = status_attendance

#         # Update remarks only if provided
#         if remarks is not None:
#             attendance_record.remarks = remarks

#         # Update check-in time only if provided
#         if checked_in_time is not None:
#             attendance_record.checked_in_time = checked_in_time

#         # Update check-out time only if provided
#         if checked_out_time is not None:
#             attendance_record.checked_out_time = checked_out_time

#         # Optional: clear times when absent
#         if status_attendance == "Absent":
#             attendance_record.checked_in_time = None
#             attendance_record.checked_out_time = None

#         attendance_record.save()

#         return Response({
#             "status": True,
#             "message": (
#                 "Teacher attendance updated successfully"
#                 if not created
#                 else "Teacher attendance marked successfully"
#             ),
#             "attendance": {
#                 "attendance_id": attendance_record.id,
#                 "teacher_id": teacher.id,
#                 "teacher_name": teacher.staff_name,
#                 "teacher_department": teacher.department,
#                 "date": attendance_record.date,
#                 "status": attendance_record.status,
#                 "remarks": attendance_record.remarks,
#                 "checked_in_time": attendance_record.checked_in_time,
#                 "checked_out_time": attendance_record.checked_out_time,
#             }
#         }, status=status.HTTP_200_OK)

# mark attendance to teachers
class MarkTeachersAttendance(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = MarkTeachersAttendanceSerializer(
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        teacher_id = serializer.validated_data.get("teacher_id")
        date = serializer.validated_data.get("date")

        if not teacher_id or not date:
            return Response({
                "status": False,
                "message": "teacher_id and date are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        teacher = StaffManagementModel.objects.filter(
            id=teacher_id,
            designation="Teacher",
            is_teacher=True
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher not found"
            }, status=status.HTTP_404_NOT_FOUND)

        attendance_record, created = TeacherstaffAttendance.objects.get_or_create(
            teacher=teacher,
            date=date,
            defaults={
        "is_staff": False
    })
        attendance_record.is_staff = False


        

        # Partial updates
        if "status" in serializer.validated_data:
            attendance_record.status = serializer.validated_data["status"]

            if serializer.validated_data["status"] == "Absent":
                attendance_record.checked_in_time = None
                attendance_record.checked_out_time = None

        if "remarks" in serializer.validated_data:
            attendance_record.remarks = serializer.validated_data["remarks"]

        if "checked_in_time" in serializer.validated_data:
            attendance_record.checked_in_time = serializer.validated_data["checked_in_time"]

        if "checked_out_time" in serializer.validated_data:
            attendance_record.checked_out_time = serializer.validated_data["checked_out_time"]

        attendance_record.save()

        return Response({
            "status": True,
            "message": (
                "Teacher attendance updated successfully"
                if not created
                else "Teacher attendance marked successfully"
            ),
            "attendance": {
                "attendance_id": attendance_record.id,
                "teacher_id": teacher.id,
                "teacher_name": teacher.staff_name,
                "teacher_department": teacher.department,
                "date": attendance_record.date,
                "status": attendance_record.status,
                "remarks": attendance_record.remarks,
                "checked_in_time": attendance_record.checked_in_time,
                "checked_out_time": attendance_record.checked_out_time,
            }
        }, status=status.HTTP_200_OK)
    


   # students attendance list 
class StudentAttendanceListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")
        class_id = request.query_params.get("class_id")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        classes = ClassModel.objects.all()

        if class_id:
            classes = classes.filter(id=class_id)

        response_data = []

        for cls in classes:

            total_students = StudentAcademicDetails.objects.filter(
                student_class=cls
            ).count()

            attendance_qs = StudentAttendance.objects.filter(
                students_class=cls,
                date=date
            )

            present_count = attendance_qs.filter(
                status="Present"
            ).count()

            absent_count = attendance_qs.filter(
                status="Absent"
            ).count()

            half_day_count = attendance_qs.filter(
                status="Half Day"
            ).count()

            taken_by = attendance_qs.first().taken_by if attendance_qs.exists() else None

            response_data.append({
                "class_id": cls.id,
                "class_code": getattr(cls, "class_id", ""),
                "class_name": getattr(cls, "class_name", ""),
                "section": getattr(cls, "section", ""),
                "total_students": total_students,
                "present": present_count,
                "absent": absent_count,
                "half_day": half_day_count,
                "attendance_taken_by": {
                    "id": taken_by.id if taken_by else None,
                    "name": taken_by.staff_name if taken_by else None
                } if taken_by else None,
                "incharge": {
                    "id": cls.class_teacher.id if hasattr(cls, "class_teacher") and cls.class_teacher else None,
                    "name": cls.class_teacher.staff_name if hasattr(cls, "class_teacher") and cls.class_teacher else None
                }
            })

        return Response({
            "status": True,
            "message": "Attendance list fetched successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)
    




# list staff attendance based on date
class StaffAttendanceListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        staff_members = StaffManagementModel.objects.filter(is_teacher=False)

        attendance_records = TeacherstaffAttendance.objects.filter(
            date=date,
            teacher__is_teacher=False
        )

        attendance_dict = {
            attendance.teacher_id: attendance
            for attendance in attendance_records
        }

        data = []

        for staff in staff_members:

            attendance = attendance_dict.get(staff.id)

            data.append({
                "id" : attendance.id if attendance else None,

                "profile_id": staff.id,
                "staff_id": staff.profiles.user_id,
                "staff_name": staff.staff_name,
                "staff_department": staff.department,
                "date": date,
                "status": attendance.status if attendance else "Not Marked",
                "remarks": attendance.remarks if attendance else None,
                "checked_in_time": attendance.checked_in_time if attendance else None,
                "checked_out_time": attendance.checked_out_time if attendance else None,
            })

        # Pagination
        paginator = ListPagination()

        paginated_data = paginator.paginate_queryset(
            data,
            request
        )

        return paginator.get_paginated_response({
            "status": True,
            "message": "Staff attendance records retrieved successfully",
            "attendance": paginated_data
        })






  # mark staff attendance   
class MarkStaffAttendanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = MarkStaffAttendanceSerializer(
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        staff_id = serializer.validated_data.get("staff_id")
        date = serializer.validated_data.get("date")

        if not staff_id or not date:
            return Response({
                "status": False,
                "message": "staff_id and date are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        teacher = StaffManagementModel.objects.filter(
            id=staff_id,
            designation="Teacher",
            is_teacher=False
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher not found"
            }, status=status.HTTP_404_NOT_FOUND)

        attendance_record, created = TeacherstaffAttendance.objects.get_or_create(
            teacher=teacher,
            date=date,
            defaults={
        "is_staff": True
    })
        attendance_record.is_staff = True


        

        # Partial updates
        if "status" in serializer.validated_data:
            attendance_record.status = serializer.validated_data["status"]

            if serializer.validated_data["status"] == "Absent":
                attendance_record.checked_in_time = None
                attendance_record.checked_out_time = None

        if "remarks" in serializer.validated_data:
            attendance_record.remarks = serializer.validated_data["remarks"]

        if "checked_in_time" in serializer.validated_data:
            attendance_record.checked_in_time = serializer.validated_data["checked_in_time"]

        if "checked_out_time" in serializer.validated_data:
            attendance_record.checked_out_time = serializer.validated_data["checked_out_time"]

        attendance_record.save()

        return Response({
            "status": True,
            "message": (
                "Staffs attendance updated successfully"
                if not created
                else "Staffs attendance marked successfully"
            ),
            "attendance": {
                "attendance_id": attendance_record.id,
                "staff_id": teacher.id,
                "staff_name": teacher.staff_name,
                "teacher_department": teacher.department,
                "date": attendance_record.date,
                "status": attendance_record.status,
                "remarks": attendance_record.remarks,
                "checked_in_time": attendance_record.checked_in_time,
                "checked_out_time": attendance_record.checked_out_time,
            }
        }, status=status.HTTP_200_OK)
    
# export  excel sheet for teachers attedance , students attendance and also for staffs attendance

# export teachers attendance excel sheet based on date , department 
class ExportExcelTeachersAttendanceAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            selected_date = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)

        teachers = StaffManagementModel.objects.filter(
            designation="Teacher",
            is_teacher=True
        ).select_related("profiles")

        attendance_records = TeacherstaffAttendance.objects.filter(
            date=selected_date
        )

        attendance_dict = {
            attendance.teacher_id: attendance
            for attendance in attendance_records
        }

        teacher_level_map = defaultdict(list)

        timetable_data = TeachersTimeTable.objects.select_related(
            "class_assigned"
        ).values(
            "teacher_id",
            "class_assigned__level"
        ).distinct()

        for item in timetable_data:

            level = item.get("class_assigned__level")

            if level and level not in teacher_level_map[item["teacher_id"]]:
                teacher_level_map[item["teacher_id"]].append(level)

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Teacher Attendance"

        headers = [
            "Teacher ID",
            "Teacher Name",
            "Department",
            "Level",
            "Date",
            "Status",
            "Remarks",
            "Check In Time",
            "Check Out Time"
        ]

        for col_num, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)

        row_num = 2

        for teacher in teachers:

            attendance = attendance_dict.get(teacher.id)

            levels = ", ".join(
                map(str, teacher_level_map.get(teacher.id, []))
            )

            worksheet.cell(
                row=row_num,
                column=1,
                value=teacher.profiles.user_id if teacher.profiles else ""
            )

            worksheet.cell(
                row=row_num,
                column=2,
                value=teacher.staff_name
            )

            worksheet.cell(
                row=row_num,
                column=3,
                value=teacher.department
            )

            worksheet.cell(
                row=row_num,
                column=4,
                value=levels
            )

            worksheet.cell(
                row=row_num,
                column=5,
                value=str(selected_date)
            )

            worksheet.cell(
                row=row_num,
                column=6,
                value=attendance.status if attendance else "Not Marked"
            )

            worksheet.cell(
                row=row_num,
                column=7,
                value=attendance.remarks if attendance else ""
            )

            worksheet.cell(
                row=row_num,
                column=8,
                value=str(attendance.checked_in_time) if attendance and attendance.checked_in_time else ""
            )

            worksheet.cell(
                row=row_num,
                column=9,
                value=str(attendance.checked_out_time) if attendance and attendance.checked_out_time else ""
            )

            row_num += 1

        # Auto adjust column width
        for column in worksheet.columns:
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

            worksheet.column_dimensions[column_letter].width = max_length + 5

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response[
            "Content-Disposition"
        ] = f'attachment; filename="Teacher_Attendance_{selected_date}.xlsx"'

        workbook.save(response)

        return response



#  export excel  students attendance api 
class ExportStudentAttendanceExcelAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")
        class_id = request.query_params.get("class_id")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        classes = ClassModel.objects.all()

        if class_id:
            classes = classes.filter(id=class_id)

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Student Attendance"

        headers = [
            "Class Code",
            "Class Name",
            "Section",
            "Total Students",
            "Present",
            "Absent",
            "Half Day",
            "Attendance Taken By",
            "Class Incharge"
        ]

        for col_num, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)

        row_num = 2

        for cls in classes:

            total_students = StudentAcademicDetails.objects.filter(
                student_class=cls
            ).count()

            attendance_qs = StudentAttendance.objects.filter(
                students_class=cls,
                date=date
            )

            present_count = attendance_qs.filter(
                status="Present"
            ).count()

            absent_count = attendance_qs.filter(
                status="Absent"
            ).count()

            half_day_count = attendance_qs.filter(
                status="Half Day"
            ).count()

            taken_by = attendance_qs.first().taken_by if attendance_qs.exists() else None

            worksheet.cell(
                row=row_num,
                column=1,
                value=getattr(cls, "class_id", "")
            )

            worksheet.cell(
                row=row_num,
                column=2,
                value=getattr(cls, "class_name", "")
            )

            worksheet.cell(
                row=row_num,
                column=3,
                value=getattr(cls, "section", "")
            )

            worksheet.cell(
                row=row_num,
                column=4,
                value=total_students
            )

            worksheet.cell(
                row=row_num,
                column=5,
                value=present_count
            )

            worksheet.cell(
                row=row_num,
                column=6,
                value=absent_count
            )

            worksheet.cell(
                row=row_num,
                column=7,
                value=half_day_count
            )

            worksheet.cell(
                row=row_num,
                column=8,
                value=taken_by.staff_name if taken_by else ""
            )

            worksheet.cell(
                row=row_num,
                column=9,
                value=cls.class_teacher.staff_name
                if hasattr(cls, "class_teacher") and cls.class_teacher
                else ""
            )

            row_num += 1

        # Auto-adjust column widths
        for column in worksheet.columns:

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

            worksheet.column_dimensions[column_letter].width = max_length + 5

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        filename = f"Student_Attendance_{date}.xlsx"

        if class_id:
            filename = f"Student_Attendance_Class_{class_id}_{date}.xlsx"

        response[
            "Content-Disposition"
        ] = f'attachment; filename="{filename}"'

        workbook.save(response)

        return response


# staffs attendance export excel api 
class ExportStaffAttendanceExcelAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.query_params.get("date")

        if not date:
            return Response({
                "status": False,
                "message": "Date query parameter is required in YYYY-MM-DD format"
            }, status=status.HTTP_400_BAD_REQUEST)

        staff_members = StaffManagementModel.objects.filter(
            is_teacher=False
        ).select_related("profiles")

        attendance_records = TeacherstaffAttendance.objects.filter(
            date=date,
            teacher__is_teacher=False
        )

        attendance_dict = {
            attendance.teacher_id: attendance
            for attendance in attendance_records
        }

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Staff Attendance"

        headers = [
            "Staff ID",
            "Staff Name",
            "Department",
            "Date",
            "Status",
            "Remarks",
            "Check In Time",
            "Check Out Time"
        ]

        for col_num, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)

        row_num = 2

        for staff in staff_members:

            attendance = attendance_dict.get(staff.id)

            worksheet.cell(
                row=row_num,
                column=1,
                value=staff.profiles.user_id if staff.profiles else ""
            )

            worksheet.cell(
                row=row_num,
                column=2,
                value=staff.staff_name
            )

            worksheet.cell(
                row=row_num,
                column=3,
                value=staff.department
            )

            worksheet.cell(
                row=row_num,
                column=4,
                value=str(date)
            )

            worksheet.cell(
                row=row_num,
                column=5,
                value=attendance.status if attendance else "Not Marked"
            )

            worksheet.cell(
                row=row_num,
                column=6,
                value=attendance.remarks if attendance else ""
            )

            worksheet.cell(
                row=row_num,
                column=7,
                value=str(attendance.checked_in_time)
                if attendance and attendance.checked_in_time
                else ""
            )

            worksheet.cell(
                row=row_num,
                column=8,
                value=str(attendance.checked_out_time)
                if attendance and attendance.checked_out_time
                else ""
            )

            row_num += 1

        # Auto-adjust column widths
        for column in worksheet.columns:

            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                if cell.value:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )

            worksheet.column_dimensions[column_letter].width = max_length + 5

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response[
            "Content-Disposition"
        ] = f'attachment; filename="Staff_Attendance_{date}.xlsx"'

        workbook.save(response)

        return response






#************************************************ dashboard views  ************************************
# dashboard kpi cards 
class DashboardKpiCardsAPIViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
       
        today = timezone.now().date()

        total_students = Profiles.objects.filter(
            role="Student").count()
        total_teachers = StaffManagementModel.objects.filter(
            designation__icontains="Teacher", is_teacher=True).count()
        total_non_teaching_staffs = StaffManagementModel.objects.filter(
            is_teacher=False).count()
        total_active_students = StudentPersonalDetails.objects.filter(
            user__is_active=True).count()
        new_admission_count = StudentPersonalDetails.objects.filter(user__date_joined = today).count()
        total_batches = ClassModel.objects.count()

        return Response({
            "status": True,
            "message": "Dashboard KPI cards data retrieved successfully",
            "data": {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_non_teaching_staffs": total_non_teaching_staffs,
                "total_active_students": total_active_students,
                "new_admission_count": new_admission_count,
                "total_batches": total_batches
            }
        }, status=status.HTTP_200_OK)
    


# student admission trend pie chart current years students data for pie chart  based on level wise(high school , lp , up)
class DashboardStudentPieChartBatchCountAPIViews(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Pie Chart Data (Class / Level wise)
        class_wise_students = (
            StudentAcademicDetails.objects
            .filter(student_class__isnull=False)
            .values(
                "student_class__level"
            )
            .annotate(
                count=Count("id")
            )
            .order_by()
        )

        pie_chart_data = []

        for item in class_wise_students:
            pie_chart_data.append({
                "label": item["student_class__level"],
                "value": item["count"]
            })

        # Bar Chart Data (Batch Wise)
        batch_wise_students = (
            StudentAcademicDetails.objects
            .exclude(batch__isnull=True)
            .exclude(batch="")
            .values("batch")
            .annotate(
                count=Count("id")
            )
            .order_by("batch")
        )

        bar_chart_data = []

        for item in batch_wise_students:
            bar_chart_data.append({
                "batch": item["batch"],
                "count": item["count"]
            })

        return Response({
            "status": True,
            "message": "Dashboard data fetched successfully",

            "student_admission_trend": pie_chart_data,

            "batch_wise_student_count": bar_chart_data
        }, status=status.HTTP_200_OK)



        