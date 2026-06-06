from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from django.utils import timezone
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from administration_app.pagination import ListPagination
from django.db.models.functions import Lower
from datetime import datetime, timedelta
# Create your views here.

# change passsword 
class TeacherChangePasswordAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        user = request.user

        # Check old password
        if not user.check_password(old_password):
            return Response(
                {
                    "status": False,
                    "message": "Old password is incorrect"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check new password match
        if new_password != confirm_password:
            return Response(
                {
                    "status": False,
                    "message": "New password and confirm password do not match"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Change password
        user.set_password(new_password)
        user.save()

        return Response(
            {
                "status": True,
                "message": "Password changed successfully"
            },
            status=status.HTTP_200_OK
        )

# get login teachers profile details 
class TeacherProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        print("USER ID:", request.user.id)
        print("USER:", request.user.user_id)

        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        print("TEACHER:", teacher)

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeacherProfileSerializer(teacher)

        return Response({
            "status": True,
            "message": "Teacher profile retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    


# login teachers time table 
class TeacherTimeTableGetAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        timetable_data = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

        # Regular timetable
        timetables = TeachersTimeTable.objects.filter(
            teacher=teacher,
            teacher__profiles__category=request.user.category
        ).select_related(
            "class_assigned"
        ).order_by("day_of_week", "period")

        for timetable in timetables:

            timetable_data[timetable.day_of_week].append({
                "id": timetable.id,
                "period": timetable.period,
                "subject": timetable.subject,
                "class_assigned": (
                    timetable.class_assigned.class_name
                    if timetable.class_assigned else None
                ),
                "is_substitution": False
            })

        # Today's substitution assignments
        today = timezone.now().date()
        today_day = today.strftime("%A")

        substitute_assignments = SubstituteTeacherAssignment.objects.filter(
            substitute_teacher=teacher,
            date=today
        ).select_related(
            "class_assigned",
            "original_teacher"
        )

        for assignment in substitute_assignments:

            timetable_data[today_day].append({
                "id": assignment.id,
                "period": assignment.period,
                "subject": assignment.subject,
                "class_assigned": assignment.class_assigned.class_name,
                "is_substitution": True,
                "original_teacher": assignment.original_teacher.staff_name,
                "substitution_date": assignment.date
            })

        # Sort periods within each day
        for day in timetable_data:
            timetable_data[day] = sorted(
                timetable_data[day],
                key=lambda x: x["period"]
            )

        category_name = (
            teacher.profiles.category.name
            if teacher.profiles.category else None
        )

        return Response({
            "status": True,
            "message": "Timetable fetched successfully",
            "teacher_id": teacher.id,
            "teacher_name": teacher.staff_name,
            "category": category_name,
            "today": today,
            "timetable": timetable_data
        }, status=status.HTTP_200_OK)
    


# list all classes  based on login teachers category api 
class TeacherClassListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        classes = ClassModel.objects.filter(
            category=teacher.profiles.category
        ).select_related(
            "class_teacher"
        ).order_by("class_name")

        class_data = []

        for cls in classes:

            class_data.append({
                "id": cls.id,
                "class_name": f"{cls.class_name}  {cls.section}"
                # "batch": cls.batch,
                # "section": cls.section,
                # "class_teacher": (
                #     cls.class_teacher.staff_name
                #     if cls.class_teacher else None
                # )
            })

        return Response({
            "status": True,
            "message": "Classes fetched successfully",
            "classes": class_data
        }, status=status.HTTP_200_OK)
    



    
# list students attendance api 
class StudentAttendanceListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        class_id = request.GET.get("class_id")
        attendance_date = request.GET.get("date")

        if not class_id:
            return Response({
                "status": False,
                "message": "class_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not attendance_date:
            return Response({
                "status": False,
                "message": "date is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        assigned_class = ClassModel.objects.filter(
            id=class_id
        ).first()

        if not assigned_class:
            return Response({
                "status": False,
                "message": "Class not found"
            }, status=status.HTTP_404_NOT_FOUND)

        students = StudentAcademicDetails.objects.filter(
            student_class=assigned_class
        ).select_related(
            "user"
        ).order_by(
            Lower("user__fullname")
        )

        attendance_records = StudentAttendance.objects.filter(
            students_class=assigned_class,
            date=attendance_date
        )

        attendance_map = {
            attendance.student_id: attendance
            for attendance in attendance_records
        }

        student_data = []

        for student in students:

            attendance = attendance_map.get(
                student.user.id
            )

            student_data.append({
                "student_id": student.user.id,
                "student_name": student.user.fullname,
                "roll_number": student.roll_number,
                "user_id": student.user.user_id,
                "attendance_status":
                    attendance.status if attendance else None,
                "remarks":
                    attendance.remarks if attendance else "",
                "reason":
                    attendance.reason if attendance else ""
            })

        total_students = students.count()

        present_count = attendance_records.filter(
            status="Present"
        ).count()

        absent_count = attendance_records.filter(
            status="Absent"
        ).count()

        others_count = attendance_records.exclude(
            status__in=["Present", "Absent"]
        ).count()

        marked_count = attendance_records.count()

        remaining_count = total_students - marked_count

        return Response({
            "status": True,
            "message": "Attendance list fetched successfully",
            "class_id": assigned_class.id,
            "class_name": assigned_class.class_name,
            "date": attendance_date,
            "total_students": total_students,
            "attendance_marked": marked_count,
            "present_count": present_count,
            "absent_count": absent_count,
            "others_count": others_count,
            "remaining_count": remaining_count,
            "students": student_data
        }, status=status.HTTP_200_OK)
    

# mark attendance api
# class MarkAttendanceAPIView(APIView):

#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         class_id = request.data.get("class_id")
#         attendance_date = request.data.get("date")
#         attendance_list = request.data.get("attendance", [])

#         if not class_id:
#             return Response({
#                 "status": False,
#                 "message": "class_id is required"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         if not attendance_date:
#             return Response({
#                 "status": False,
#                 "message": "date is required"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         assigned_class = ClassModel.objects.filter(
#             id=class_id
#         ).first()

#         if not assigned_class:
#             return Response({
#                 "status": False,
#                 "message": "Class not found"
#             }, status=status.HTTP_404_NOT_FOUND)

#         teacher = StaffManagementModel.objects.filter(
#             profiles=request.user
#         ).first()

#         if not teacher:
#             return Response({
#                 "status": False,
#                 "message": "Teacher profile not found"
#             }, status=status.HTTP_404_NOT_FOUND)

#         for item in attendance_list:

#             student_id = item.get("student_id")
#             status_value = item.get("status")
#             remarks = item.get("remarks", "")
#             reason = item.get("reason", "")

#             if not student_id or not status_value:
#                 continue

#             student = Profiles.objects.filter(
#                 id=student_id,
#                 role="Student"
#             ).first()

#             if not student:
#                 continue

#             student_exists = StudentAcademicDetails.objects.filter(
#                 user=student,
#                 student_class=assigned_class
#             ).exists()

#             if not student_exists:
#                 continue

#             StudentAttendance.objects.update_or_create(
#                 student=student,
#                 date=attendance_date,
#                 defaults={
#                     "students_class": assigned_class,
#                     "status": status_value,
#                     "remarks": remarks,
#                     "reason": reason,
#                     "taken_by": teacher
#                 }
#             )

#         return Response({
#             "status": True,
#             "message": "Attendance saved successfully"
#         }, status=status.HTTP_200_OK)
    
class MarkAttendanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        class_id = request.data.get("class_id")
        attendance_date = request.data.get("date")
        remark = request.data.get("remark", "")
        attendance_list = request.data.get("attendance", [])

        if not class_id:
            return Response({
                "status": False,
                "message": "class_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not attendance_date:
            return Response({
                "status": False,
                "message": "date is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            attendance_date_obj = datetime.strptime(
                attendance_date,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.localdate()

        # Allow editing only on attendance date and the next day
        # Example:
        # Attendance Date = 2026-06-05
        # Editable On = 2026-06-05 and 2026-06-06
        # Blocked From = 2026-06-07 onwards

        last_editable_date = attendance_date_obj + timedelta(days=1)

        if today > last_editable_date:
            return Response({
                "status": False,
                "message": "Attendance editing period has expired."
            }, status=status.HTTP_400_BAD_REQUEST)

        assigned_class = ClassModel.objects.filter(
            id=class_id
        ).first()

        if not assigned_class:
            return Response({
                "status": False,
                "message": "Class not found"
            }, status=status.HTTP_404_NOT_FOUND)

        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        for item in attendance_list:

            student_id = item.get("student_id")
            status_value = item.get("status")
            reason = item.get("reason", "")

            if not student_id or not status_value:
                continue

            student = Profiles.objects.filter(
                id=student_id,
                role="Student"
            ).first()

            if not student:
                continue

            student_exists = StudentAcademicDetails.objects.filter(
                user=student,
                student_class=assigned_class
            ).exists()

            if not student_exists:
                continue

            StudentAttendance.objects.update_or_create(
                student=student,
                date=attendance_date_obj,
                defaults={
                    "students_class": assigned_class,
                    "status": status_value,
                    "remarks": remark,
                    "reason": reason,
                    "taken_by": teacher
                }
            )

        return Response({
            "status": True,
            "message": "Attendance saved successfully"
        }, status=status.HTTP_200_OK)


# attendance history by class and date api 
class ClassAttendanceHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        attendance_date = request.GET.get("date")
        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if not attendance_date:
            return Response({
                "status": False,
                "message": "date is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        assigned_class = ClassModel.objects.filter(
            class_teacher=teacher
        ).first()

        if not assigned_class:
            return Response({
                "status": False,
                "message": "No class assigned to this teacher"
            }, status=status.HTTP_404_NOT_FOUND)

        attendance_qs = StudentAttendance.objects.filter(
            students_class=assigned_class,
            date=attendance_date
        ).select_related(
            "student",
            "taken_by"
        )

        total_students = StudentAcademicDetails.objects.filter(
            student_class=assigned_class
        ).count()

        present_count = attendance_qs.filter(
            status="Present"
        ).count()

        absent_count = attendance_qs.filter(
            status="Absent"
        ).count()

        late_count = attendance_qs.filter(
            status="Late"
        ).count()

        half_day_count = attendance_qs.filter(
            status="Half day"
        ).count()

        class_incharge = assigned_class.class_teacher.staff_name if assigned_class.class_teacher else None

        attendance_taken_by = None

        first_record = attendance_qs.first()

        if first_record and first_record.taken_by:
            attendance_taken_by = {
                "id": first_record.taken_by.id,
                "name": first_record.taken_by.staff_name,
                "staff_id": first_record.taken_by.profiles.user_id
            }

        absent_students = []
        late_students = []
        half_day_students = []

        for attendance in attendance_qs:

            student_data = {
                "student_id": attendance.student.id,
                "student_name": attendance.student.fullname,
                "user_id": attendance.student.user_id,
                "reason": attendance.reason,
                "remarks": attendance.remarks,
                "status": attendance.status
            }

            if attendance.status == "Absent":
                absent_students.append(student_data)

            elif attendance.status == "Late":
                late_students.append(student_data)

            elif attendance.status == "Half day":
                half_day_students.append(student_data)

        return Response({
            "status": True,
            "message": "Attendance history fetched successfully",

            "class": {
                "id": assigned_class.id,
                "class_name": assigned_class.class_name,
                "class_teacher": (
                    assigned_class.class_teacher.staff_name
                    if assigned_class.class_teacher
                    else None
                )
            },

            "date": attendance_date,

            "summary": {
                "total_students": total_students,
                "present": present_count,
                "absent": absent_count,
                "late": late_count,
                "half_day": half_day_count,
                "class_incharge": class_incharge
            },

            "attendance_taken_by": attendance_taken_by,

            "absent_students": absent_students,
            "late_students": late_students,
            "half_day_students": half_day_students

        }, status=status.HTTP_200_OK)


    # teacher apply leave 
class ApplyTeacherLeaveAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:
            teacher = StaffManagementModel.objects.get(
                profiles=request.user
            )
        except StaffManagementModel.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Teacher profile not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TeacherLeaveSerializer(
            data=request.data,
            context={
                "request": request,
                "teacher": teacher
            }
        )

        if serializer.is_valid():

            leave = serializer.save(
                teacher=teacher
            )

            return Response(
                {
                    "status": True,
                    "message": "Leave applied successfully",
                    "data": TeacherLeaveSerializer(leave).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    

class TeacherLeaveListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):


        leaves = TeacherLeave.objects.filter(
            teacher__profiles=request.user
        ).order_by("-created_at")

        serializer = TeacherLeaveListSerializer(
            leaves,
            many=True
        )

        return Response(
            {
                "status": True,
                "message": "Leave list fetched successfully",
                "count": leaves.count(),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

  