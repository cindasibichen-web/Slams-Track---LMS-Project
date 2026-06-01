from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from administration_app.pagination import ListPagination

# Create your views here.



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

        timetables = TeachersTimeTable.objects.filter(
            teacher_id=teacher,
            teacher__profiles__category=request.user.category
        ).order_by("day_of_week", "period")

        if not timetables.exists():
            return Response({
                "status": False,
                "message": "No timetable found for this teacher"
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

        teacher_name = timetables.first().teacher.staff_name

        for timetable in timetables:

            timetable_data[timetable.day_of_week].append({
                "id": timetable.id,
                "period": timetable.period,
                "subject": timetable.subject,
                "class_assigned": (
                    timetable.class_assigned.class_name
                    if timetable.class_assigned
                    else None
                )
            })

        return Response({
            "status": True,
            "message": "Timetable fetched successfully",
            "teacher": teacher_name,
            "timetable": timetable_data
        }, status=status.HTTP_200_OK)
    


  # list students based on login teacherss class 
class TeacherStudentsListAPIView(APIView):

    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self, request):

        teacher = StaffManagementModel.objects.filter(
            profiles=request.user
        ).first()

        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        assigned_class = ClassModel.objects.filter(
            class_teacher=teacher
        ).first()

        if not assigned_class:
            return Response({
                "status": False,
                "message": "No class assigned to this teacher"
            }, status=status.HTTP_404_NOT_FOUND)

        students = StudentsModel.objects.filter(
            student_class=assigned_class
        ).order_by("student_name")

        if not students.exists():
            return Response({
                "status": False,
                "message": "No students found for this class"
            }, status=status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        paginated_students = paginator.paginate_queryset(students, request)

        serializer = StudentSerializer(paginated_students, many=True)

        return paginator.get_paginated_response({
            "status": True,
            "message": "Students fetched successfully",
            "class": assigned_class.class_name,
            "students": serializer.data
        })  