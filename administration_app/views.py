from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from . pagination import ListPagination

# Create your views here.



# Add students 
class AddStudents(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = StudentCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            student = serializer.save()

            return Response({
                "status": True,
                "message": "Student created successfully",
                "data": StudentCreateSerializer(student).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
class StudentListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = StudentAcademicDetails.objects.select_related(
            'user',
            'student_class'
        ).all().order_by('-id')

        # Search
        search = request.GET.get('search')

        if search:
            queryset = queryset.filter(
                user__fullname__icontains=search
            )

        # Pagination
        paginator = ListPagination()

        paginated_queryset = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = StudentListSerializer(
            paginated_queryset,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )
        
        
        
        
class StudentoverviewAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, id):

        try:
            personal = StudentPersonalDetails.objects.select_related(
                "user"
            ).get(id=id)

        except StudentPersonalDetails.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Student not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        student = personal.user

        academic = StudentAcademicDetails.objects.filter(
            user=student
        ).first()

        data = {
            "personal_details_id": personal.id,
            "profile_id": student.id,

            # Header
            "student_id": student.user_id,
            "fullname": student.fullname,
            "student_photo": (
                request.build_absolute_uri(
                    student.profile_picture.url
                )
                if hasattr(student, "profile_picture")
                and student.profile_picture
                else None
            ),

            # Personal Information
            "dob": personal.dob,
            "gender": personal.gender,
            "blood_group": personal.blood_group,

            # Contact Information
            "email": student.email,
            "phone_number": student.phone_number,
            "address": personal.address,

            # Parent Information
            "father_name": personal.father_name,
            "father_phone_number": personal.father_phone_number,
            "father_occupation": personal.father_occupation,

            "mother_name": personal.mother_name,
            "mother_phone_number": personal.mother_phone_number,
            "mother_occupation": personal.mother_occupation,

            # Academic Information
            "class_name": (
                academic.student_class.class_name
                if academic and academic.student_class
                else None
            ),
            "section": academic.section if academic else None,
            "roll_number": academic.roll_number if academic else None,
            "admission_date": (
                academic.admission_date
                if academic else None
            ),
            "previous_qualifications": (
                academic.previous_qualifications
                if academic else None
            ),
            
            "previous_institute": (
                academic.previous_institute
                if academic else None
            ),
            
            "academic_status": (
                academic.status
                if academic else None
            ),
        }

        return Response(
            {
                "status": True,
                "message": "Student overview fetched successfully",
                "data": data
            },
            status=status.HTTP_200_OK
        )
    
#*************************** Staff management section views ******************************************#####
# staff management section views
class AddStaffManagementView(APIView):

    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]



    def post(self, request):

        if request.user.role == "Non-administration staff":
            return Response({
                "status": False,
                "message": "You do not have permission to create staff members."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = StaffCreateSerializer(data=request.data ,  context={'request': request})

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Staff created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    


# list teaching staff 
class ListTeachingStaffAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        staff_members = StaffManagementModel.objects.filter(
            is_teacher=True,
            profiles__category=request.user.category
        )

        paginator = ListPagination()

        paginated_queryset = paginator.paginate_queryset(
            staff_members,
            request
        )

        serializer = ListStaffSerializer(
            paginated_queryset,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

# list non teaching staff
class ListNonTeachingStaffAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        staff_members = StaffManagementModel.objects.filter(is_teacher=False, category=request.user.category)
        paginator = ListPagination()

        paginated_queryset = paginator.paginate_queryset(
            staff_members,
            request
        )

        serializer = ListStaffSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
           


# edit staffs details 
class EditStaffAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, staff_id):

        try:
            staff_member = StaffManagementModel.objects.get(id=staff_id, category=request.user.category)
        except StaffManagementModel.DoesNotExist:
            return Response({
                "status": False,
                "message": "Staff member not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EditStaffSerializer(staff_member, data=request.data, partial=True)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Staff member updated successfully",
                "data": serializer.data
             }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "errors": serializer.errors    
        })
    



#**********************Academic management views  *******************************

# class add list api 
class AddListClassAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        classes = ClassModel.objects.filter(
            category=request.user.category
        )

        paginator = ListPagination()

        paginated_classes = paginator.paginate_queryset(
            classes,
            request
        )

        data = []

        for class_instance in paginated_classes:

            data.append({
                "id": class_instance.id,
                "class_id": class_instance.class_id,
                "class_name": class_instance.class_name,
                "total_students": StudentAcademicDetails.objects.filter(
        student_class=class_instance
    ).count(),

                "subject": list(
                    class_instance.subject.values_list(
                        "name",
                        flat=True
                    )
                ),
                "level": class_instance.level,
                "section": class_instance.section,
                "class_teacher": class_instance.class_teacher.staff_name  if class_instance.class_teacher else None,
                "status": class_instance.status,
                "batch": class_instance.batch,
                "department": class_instance.department,
                "branch": class_instance.branch,
                "created_at": class_instance.created_at,
                "updated_at": class_instance.updated_at
            })

        return paginator.get_paginated_response(data)


    def post(self, request):

        serializer = AddListEditClassSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()
            category = request.user.category
            class_instance = serializer.instance
            class_instance.category = category
            class_instance.save()


            return Response({
                "status": True,
                "message": "Class created successfully",
                "data": serializer.data
             }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors    
        })


      # edit class  api 

class EditClassAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, class_id):

        try:
            class_instance = ClassModel.objects.get(id=class_id, category=request.user.category)
        except ClassModel.DoesNotExist:
            return Response({
                "status": False,
                "message": "Class not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AddListEditClassSerializer(class_instance, data=request.data, partial=True)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Class updated successfully",
                "data": serializer.data
             }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "errors": serializer.errors    
        })
    
# filter classes 

class FilterClassByBatchAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, batch):

        classes = ClassModel.objects.filter(batch=batch, category=request.user.category)
        paginator = ListPagination()

        paginated_classes = paginator.paginate_queryset(
            classes,
            request
        )

        data = []

        for class_instance in paginated_classes:

            data.append({
                "id": class_instance.id,
                "class_id": class_instance.class_id,
                "class_name": class_instance.class_name,
                "total_students": StudentAcademicDetails.objects.filter(
        student_class=class_instance
    ).count(),

                "subject": list(
                    class_instance.subject.values_list(
                        "name",
                        flat=True
                    )
                ),
                "level": class_instance.level,
                "section": class_instance.section,
                "class_teacher": class_instance.class_teacher.staff_name  if class_instance.class_teacher else None,
                "status": class_instance.status,
                "batch": class_instance.batch,
                "department": class_instance.department,
                "branch": class_instance.branch,
                "created_at": class_instance.created_at,
                "updated_at": class_instance.updated_at
            })

        return paginator.get_paginated_response(data)
    


# add time table for teachers 
class AddTeacherTimeTableAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = TeacherTimeTableSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()
            category = request.user.category
            class_instance = serializer.instance
            class_instance.category = category
            class_instance.save()

            return Response({
                "status": True,
                "message": "Time table created successfully",
                "data": serializer.data
             }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors    
        })
    
# list each teachers timetable 
class ListTeacherTimeTableAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request , teacher_id):

        if not teacher_id:
            return Response({
                "status": False,
                "message": "teacher_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        timetables = TeachersTimeTable.objects.filter(
            teacher_id=teacher_id,
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
    


# edit teachers timetable 
class EditTeacherTimeTableAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, timetable_id):

        try:
            timetable_instance = TeachersTimeTable.objects.get(id=timetable_id, teacher__profiles__category=request.user.category)
        except TeachersTimeTable.DoesNotExist:
            return Response({
                "status": False,
                "message": "Timetable entry not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeacherTimeTableSerializer(timetable_instance, data=request.data, partial=True)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Timetable entry updated successfully",
                "data": serializer.data
             }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "errors": serializer.errors    
        })