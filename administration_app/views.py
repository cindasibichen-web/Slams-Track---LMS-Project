from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from . pagination import ListPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q , Sum
from datetime import timedelta 
from django.db.models import Count
# Create your views here.


#****************************************************** student management section ********************************************************************
# Add students 

class StudentDashboardKPIAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Date Filter
        date_param = request.GET.get("date")

        if date_param:
            try:
                filter_date = datetime.strptime(
                    date_param,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Date format should be YYYY-MM-DD"
                }, status=400)
        else:
            filter_date = date.today()

        # Class Filter (ClassModel PK)
        class_id = request.GET.get("class_id")

        # Student Academic queryset
        academic_queryset = StudentAcademicDetails.objects.all()

        if class_id:
            academic_queryset = academic_queryset.filter(
                student_class_id=class_id
            )

        # Total Students
        total_students = academic_queryset.count()

        # Student IDs of selected class
        student_ids = academic_queryset.values_list(
            "user_id",
            flat=True
        )

        # Attendance queryset
        attendance_queryset = StudentAttendance.objects.filter(
            student_id__in=student_ids,
            date=filter_date
        )

        # Present
        present_students = attendance_queryset.filter(
            status="Present"
        ).count()

        # Absent
        absent_students = attendance_queryset.filter(
            status="Absent"
        ).count()

        # Applications Received
        applications_received = academic_queryset.filter(
            admission_date__year=filter_date.year
        ).count()

        # Fee Pending
        fee_pending = StudentFinancialDetails.objects.filter(
            user_id__in=student_ids
        ).filter(
            Q(balance_amount__gt=0) |
            Q(paid_amount__isnull=True) |
            Q(paid_amount=0)
        ).distinct().count()

        return Response({
            "status": True,
            "data": {
                "date": filter_date,
                "class_id": class_id,
                "total_students": total_students,
                "present_students": present_students,
                "absent_students": absent_students,
                "applications_received": applications_received,
                "fee_pending": fee_pending
            }
        })
class AddStudents(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = StudentCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            student = serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Student created successfully",
                    "data": StudentCreateSerializer(student).data
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
        
class StudentListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = StudentAcademicDetails.objects.filter(user__category=request.user.category
).select_related(
            'user',
            'student_class'
        ).all().order_by('-id')

        # -----------------------
        # SEARCH FILTER
        # -----------------------
        search = request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(user__fullname__icontains=search) |
                Q(user__user_id__icontains=search)
            )

        # -----------------------
        # CLASS FILTER (PRIMARY KEY FIXED)
        # -----------------------
        class_id = request.GET.get('class_id')

        if class_id:
            queryset = queryset.filter(
                student_class_id=class_id
            )

        # -----------------------
        # DATE (REQUIRED)
        # -----------------------
        attendance_date = request.GET.get('date')

        if not attendance_date:
            return Response({
                "status": False,
                "message": "date parameter is required. Example: ?date=2026-06-05"
            }, status=400)

        try:
            attendance_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }, status=400)

        # -----------------------
        # ATTENDANCE FILTER
        # -----------------------
        attendance_queryset = StudentAttendance.objects.filter(
            date=attendance_date
        )

        status_filter = request.GET.get('status')

        if status_filter and status_filter.lower() != 'all':
            attendance_queryset = attendance_queryset.filter(
                status__iexact=status_filter
            )

        student_ids = attendance_queryset.values_list('student_id', flat=True)

        queryset = queryset.filter(
            user_id__in=student_ids
        )

        # -----------------------
        # PAGINATION
        # -----------------------
        paginator = ListPagination()

        paginated_queryset = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = StudentListSerializer(
            paginated_queryset,
            many=True,
            context={
                "attendance_date": attendance_date
            }
        )

        return paginator.get_paginated_response(serializer.data)
        
        
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

        # Academic Details
        academic = StudentAcademicDetails.objects.filter(
            user=student
        ).first()

        # Financial Details
        financial = StudentFinancialDetails.objects.filter(
            user=student
        ).first()

        # Document Details
        documents = StudentDocumentDetails.objects.filter(
            user=student
        ).first()

        # Last 6 Months Leave Details (Absent Only)
        six_months_ago = timezone.now().date() - timedelta(days=180)

        absent_attendance = StudentAttendance.objects.filter(
            student=student,
            status="Absent",
            date__gte=six_months_ago
        ).order_by("-date")

        leave_details = [
            {
                "date": attendance.date,
                "reason": attendance.reason,
                "remarks": attendance.remarks
            }
            for attendance in absent_attendance
        ]

        data = {

            # Header Section
            "personal_details_id": personal.id,
            "profile_id": student.id,
            "student_id": student.user_id,
            "fullname": student.fullname,

            "student_photo": (
                request.build_absolute_uri(student.profile_picture.url)
                if getattr(student, "profile_picture", None)
                else None
            ),

            # Personal Information
            "dob": personal.dob,
            "gender": personal.gender,
            "blood_group": personal.blood_group,
            "address": personal.address,

            # Contact Information
            "email": student.email,
            "phone_number": student.phone_number,

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
            "batch": academic.batch if academic else None,
            "roll_number": academic.roll_number if academic else None,
            "student_type": academic.student_type if academic else None,
            "admission_id": academic.admission_id if academic else None,
            "admission_date": academic.admission_date if academic else None,
            "previous_institute": (
                academic.previous_institute
                if academic else None
            ),
            "previous_qualifications": (
                academic.previous_qualifications
                if academic else None
            ),
            "academic_status": (
                academic.status
                if academic else None
            ),

            # Financial Information
            "admission_amount": (
                financial.admission_amount
                if financial else None
            ),
            "course_fee": (
                financial.course_fee
                if financial else None
            ),
            "discount": (
                financial.discount
                if financial else None
            ),
            "paid_amount": (
                financial.paid_amount
                if financial else None
            ),
            "balance_amount": (
                financial.balance_amount
                if financial else None
            ),
            "payment_mode": (
                financial.payment_mode
                if financial else None
            ),
            "installment_plan": (
                financial.installment_plan
                if financial else None
            ),

            # Documents
            "birth_certificate": (
                request.build_absolute_uri(
                    documents.birth_certificate.url
                )
                if documents and documents.birth_certificate
                else None
            ),
            "previous_school_tc": (
                request.build_absolute_uri(
                    documents.previous_school_tc.url
                )
                if documents and documents.previous_school_tc
                else None
            ),
            "aadhar_card": (
                request.build_absolute_uri(
                    documents.aadhar_card.url
                )
                if documents and documents.aadhar_card
                else None
            ),
            "parent_id_proof": (
                request.build_absolute_uri(
                    documents.parent_id_proof.url
                )
                if documents and documents.parent_id_proof
                else None
            ),
            "caste_certificate": (
                request.build_absolute_uri(
                    documents.caste_certificate.url
                )
                if documents and documents.caste_certificate
                else None
            ),

            # Leave Details (Last 6 Months)
            "total_leave_days": absent_attendance.count(),
            "leave_details": leave_details
        }

        return Response(
            {
                "status": True,
                "message": "Student overview fetched successfully",
                "data": data
            },
            status=status.HTTP_200_OK
        )
     
class StudentCheckAdmissionIdAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        admission_id = request.query_params.get("admission_id")

        if not admission_id:
            return Response(
                {
                    "status": False,
                    "message": "Admission ID is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        exists = StudentAcademicDetails.objects.filter(
            admission_id__iexact=admission_id.strip()
        ).exists()

        if exists:
            return Response(
                {
                    "status": False,
                    "exists": True,
                    "message": "Admission ID already exists"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": True,
                "exists": False,
                "message": "Admission ID is available"
            },
            status=status.HTTP_200_OK
        )        



class StudentEditAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request, profile_id):

        try:
            student = Profiles.objects.get(
                id=profile_id,
                role="Student"
            )

        except Profiles.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Student not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # Profile Update
        student.fullname = data.get(
            "fullname",
            student.fullname
        )
        student.email = data.get(
            "email",
            student.email
        )
        student.phone_number = data.get(
            "phone_number",
            student.phone_number
        )
        student.save()

        # Personal Details
        personal, _ = StudentPersonalDetails.objects.get_or_create(
            user=student
        )

        for field in [
            "dob",
            "gender",
            "address",
            "blood_group",
            "father_name",
            "father_phone_number",
            "father_occupation",
            "mother_name",
            "mother_phone_number",
            "mother_occupation",
        ]:
            if field in data:
                setattr(personal, field, data[field])

        personal.save()

        # Academic Details
        academic, _ = StudentAcademicDetails.objects.get_or_create(
            user=student
        )

        if "student_class" in data:
            academic.student_class_id = data["student_class"]

        for field in [
            "batch",
            "roll_number",
            "section",
            "student_type",
            "admission_id",
            "admission_date",
            "previous_institute",
            "previous_qualifications",
            "status",
        ]:
            if field in data:
                setattr(academic, field, data[field])

        academic.save()

        # Financial Details
        financial, _ = StudentFinancialDetails.objects.get_or_create(
            user=student
        )

        for field in [
            "admission_amount",
            "course_fee",
            "discount",
            "paid_amount",
            "payment_mode",
            "balance_amount",
            "installment_plan",
        ]:
            if field in data:
                setattr(financial, field, data[field])

        financial.save()

        # Document Details
        documents, _ = StudentDocumentDetails.objects.get_or_create(
            user=student
        )

        for field in [
            "student_photo",
            "birth_certificate",
            "previous_school_tc",
            "aadhar_card",
            "parent_id_proof",
            "caste_certificate",
        ]:
            if field in data:
                setattr(documents, field, data[field])

        documents.save()

        return Response(
            {
                "status": True,
                "message": "Student details updated successfully"
            },
            status=status.HTTP_200_OK
        )
    






#*************************** Staff management section views ******************************************#####

# staff management kpi cards view 
class StaffManagementKPICards(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pass


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
        if request.user.role == "SuperAdmin":
            staff_members = StaffManagementModel.objects.all()
        else:


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

        if request.user.role == "SuperAdmin":
            staff_members = StaffManagementModel.objects.all()
        else:


            staff_members = StaffManagementModel.objects.filter(is_teacher=False, profiles__category=request.user.category)
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
            staff_member = StaffManagementModel.objects.get(id=staff_id)
        except StaffManagementModel.DoesNotExist:
            return Response({
                "status": False,
                "message": "Staff member not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = StaffCreateSerializer(staff_member, data=request.data, partial=True)

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
    


#kpi cards api 
# class SatffManagementKPICardsAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):

#         total_staffs = StaffManagementModel.objects.filter(profiles__category=request.user.category).count()

#         total_teaching_staff = StaffManagementModel.objects.filter(
#             is_teacher=True,
#             profiles__category=request.user.category
#         ).count()

#         total_non_teaching_staff = StaffManagementModel.objects.filter(
#             is_teacher=False,
#             profiles__category=request.user.category
#         ).count()

#         present_teachers_today = TeacherLeave.objects.filter(
#             teacher__profiles__category=request.user.category,
#             status="Approved",
#             from_date__lte=timezone.now().date(),
#             to_date__gte=timezone.now().date()
#         ).count()

#         absent_teachers_today = TeacherLeave.objects.filter(
#             teacher__profiles__category=request.user.category,
#             status="Pending",
#             from_date__lte=timezone.now().date(),
#             to_date__gte=timezone.now().date()
#         ).count()



#         return Response({
#             "status": True,
#             "message": "Staff management KPI cards fetched successfully",
#             "data": {
#                 "total_staffs": total_staffs,
#                 "total_teaching_staff": total_teaching_staff,
#                 "total_non_teaching_staff": total_non_teaching_staff,
#                 "present_teachers_today": present_teachers_today
#             }
#         }, status=status.HTTP_200_OK)




#**********************Academic management views  *******************************

# kpi cards 
class AcademicManagementKPICardsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self , request):
        total_students = StudentPersonalDetails.objects.count(request.user.category)
        total_teachers = StaffManagementModel.objects.filter(is_teacher=True,category=request.user.category).count()
        total_administration_staff = StaffManagementModel.objects.filter(profiles__role="Administration staff").count()
        total_non_administration_staff = StaffManagementModel.objects.filter(profiles__role="Non-administration staff").count()


        return Response({
            "status ": True , 
            "Message" : "KPI cards details listed successfully",
            "data" : {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_administration_staff": total_administration_staff,
                "total_non_administration_staff": total_non_administration_staff
            }

        })




       

# class add list api 
class AddListClassAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.role == "SuperAdmin":
            classes = ClassModel.objects.all()
        else:


         classes = ClassModel.objects.filter(
            category=request.user.category
        ).annotate(
            total_students=Count("studentacademicdetails")
        )

        paginator = ListPagination()

        paginated_classes = paginator.paginate_queryset(
            classes,
            request
        )

        data = []

        for cls in paginated_classes:
            data.append({
                "id": cls.id,
                "class_id": cls.class_id,
                "class_name": cls.class_name,
                "level": cls.level,
                "section": cls.section,
                "total_students": cls.total_students,
                "status": cls.status
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

#*************************** Assign substitute teacher section views ******************************************#####
# todays absent teachers list api 
class TodaysAbsentTeachersAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        




         
        today = timezone.now().date()
        absent_teachers_qs = TeacherLeave.objects.filter(teacher__profiles__category=request.user.category,
            from_date__lte=today,
            to_date__gte=today,
            # status="Approved"
        ).select_related(
            "teacher"
        )

        if request.user.role == "SuperAdmin":
            absent_teachers_qs = TeacherLeave.objects.filter(
                from_date__lte=today,
                to_date__gte=today,
                # status="Approved"
            ).select_related(
                "teacher"
            )


        absent_teachers = []

        for leave in absent_teachers_qs:

            teacher = leave.teacher

            absent_teachers.append({
                "teacher_id": teacher.id,
                "role": teacher.profiles.role,
                "teacher_name": teacher.staff_name,
                "user_id": teacher.profiles.user_id,
                "leave_start_date": leave.from_date,
                "leave_end_date": leave.to_date,
                "leave_reason": leave.reason
            })

        return Response({
            "status": True,
            "message": "Today's absent teachers fetched successfully",
            "category": teacher.profiles.category.name,
            "date": today,
            "absent_teachers_count": len(absent_teachers),
            "absent_teachers": absent_teachers,
         
        }, status=status.HTTP_200_OK)  



  # get teacher todays timetable by teacher id 
class TeacherTodaysTimeTableAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, teacher_id):

        # Get current day of the week (e.g., Monday, Tuesday)
        today = timezone.now().strftime('%A')

        timetables = TeachersTimeTable.objects.filter(
            teacher=teacher_id,
            day_of_week=today,
            teacher__profiles__category=request.user.category
        ).select_related(
            "teacher",
            "class_assigned"
        ).order_by('period')

        if not timetables.exists():
            return Response({
                "status": False,
                "message": f"No timetable found for this teacher on {today}"
            }, status=status.HTTP_404_NOT_FOUND)
        
        

        timetable_data = []
        for item in timetables:
            timetable_data.append({
                "id": item.id,
                "day_of_week": item.day_of_week,
                "period": item.period,
                "subject": item.subject,
                "teacher_name": item.teacher.staff_name,
                "class_assigned": {
                    "id": item.class_assigned.id,
                    "class_name": item.class_assigned.class_name,
                    "section": item.class_assigned.section
                }
            })

        return Response({
            "status": True,
            "message": f"Today's ({today}) timetable fetched successfully",
            "data": timetable_data
        }, status=status.HTTP_200_OK)



# list the avilable teachers for substitute teacher assignment api
class AvailableSubstituteTeachersAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        teacher_id = request.data.get("teacher_id")
        period = request.data.get("period")
        class_id = request.data.get("class_id")

        if not teacher_id or not period or not class_id:
            return Response({
                "status": False,
                "message": "teacher_id, period and class_id are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        today_day = today.strftime("%A")

        # Teachers on leave today
        absent_teacher_ids = TeacherLeave.objects.filter(
            from_date__lte=today,
            to_date__gte=today,
            status="Approved"
        ).values_list("teacher_id", flat=True)

        # Teachers already handling a class in this period
        busy_teacher_ids = TeachersTimeTable.objects.filter(
            day_of_week=today_day,
            period=period
        ).values_list("teacher_id", flat=True)

        available_teachers = StaffManagementModel.objects.filter(
            profiles__category=request.user.category,profiles__role="Administration staff",is_teacher=True
        ).exclude(
            id__in=busy_teacher_ids
        ).exclude(
            id__in=absent_teacher_ids
        ).exclude(
            id=teacher_id
        ).select_related("profiles").order_by("staff_name")

        data = []

        for teacher in available_teachers:
            data.append({
                "teacher_id": teacher.id,
                "teacher_name": teacher.staff_name,
                "user_id": teacher.profiles.user_id
            })

        return Response({
            "status": True,
            "message": "Available substitute teachers fetched successfully",
            "teacher_id": teacher_id,
            "period": period,
            "class_id": class_id,
            "available_teachers_count": len(data),
            "available_teachers": data
        })


# assign substitute teacher api
class AssignSubstituteTeacherAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        class_id = request.data.get("class_id")
        date = request.data.get("date")
        period = request.data.get("period")
        original_teacher_id = request.data.get("original_teacher_id")
        substitute_teacher_id = request.data.get("substitute_teacher_id")

        if not all([
            class_id,
            date,
            period,
            original_teacher_id,
            substitute_teacher_id
        ]):
            return Response({
                "status": False,
                "message": "class_id, date, period, original_teacher_id and substitute_teacher_id are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        assigned_class = ClassModel.objects.filter(
            id=class_id
        ).first()

        if not assigned_class:
            return Response({
                "status": False,
                "message": "Class not found"
            }, status=status.HTTP_404_NOT_FOUND)

        original_teacher = StaffManagementModel.objects.filter(
            id=original_teacher_id
        ).first()

        if not original_teacher:
            return Response({
                "status": False,
                "message": "Original teacher not found"
            }, status=status.HTTP_404_NOT_FOUND)

        substitute_teacher = StaffManagementModel.objects.filter(
            id=substitute_teacher_id
        ).first()

        if not substitute_teacher:
            return Response({
                "status": False,
                "message": "Substitute teacher not found"
            }, status=status.HTTP_404_NOT_FOUND)

        timetable = TeachersTimeTable.objects.filter(
            teacher=original_teacher,
            class_assigned=assigned_class,
            period=period
        ).first()

        subject = timetable.subject if timetable else ""

        assignment, created = SubstituteTeacherAssignment.objects.update_or_create(
            class_assigned=assigned_class,
            date=date,
            period=period,
            defaults={
                "subject": subject,
                "original_teacher": original_teacher,
                "substitute_teacher": substitute_teacher
            }
        )

        return Response({
            "status": True,
            "message": "Substitute teacher assigned successfully",
            "assignment_id": assignment.id,
            "created": created
        })
    

# list the subtitution teacher assignment for a particular date api
class ListSubstituteTeacherAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        date = request.GET.get("date")

        if not date:
            return Response({
                "status": False,
                "message": "date is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        assignments = SubstituteTeacherAssignment.objects.filter(
            date=date,
            class_assigned__category=request.user.category
        ).select_related(
            "class_assigned",
            "original_teacher",
            "substitute_teacher"
        ).order_by("period")

        data = []

        for assignment in assignments:
            data.append({
                "assignment_id": assignment.id,
                "class_id": assignment.class_assigned.id,
                "class_name": assignment.class_assigned.class_name,
                "period": assignment.period,
                "subject": assignment.subject,
                "original_teacher_id": assignment.original_teacher.id,
                "original_teacher_name": assignment.original_teacher.staff_name,
                "substitute_teacher_id": assignment.substitute_teacher.id,
                "substitute_teacher_name": assignment.substitute_teacher.staff_name,
                "reason": assignment.reason
            })

        return Response({
            "status": True,
            "message": f"Substitute teacher assignments for {date} fetched successfully",
            "assignments_count": len(data),
            "assignments": data
        }, status=status.HTTP_200_OK)
    

# get subsititude details by substitute assignment id api 
class SubstituteTeacherAssignmentDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request, assignment_id):

        try:
            assignment = SubstituteTeacherAssignment.objects.select_related(
                "class_assigned",
                "original_teacher",
                "substitute_teacher"
            ).get(id=assignment_id, class_assigned__category=request.user.category)

            data = {
                "assignment_id": assignment.id,
                "class_id": assignment.class_assigned.id,
                "class_name": assignment.class_assigned.class_name,
                "period": assignment.period,
                "subject": assignment.subject,
                "original_teacher_id": assignment.original_teacher.id,
                "original_teacher_name": assignment.original_teacher.staff_name,
                "substitute_teacher_id": assignment.substitute_teacher.id,
                "substitute_teacher_name": assignment.substitute_teacher.staff_name,
                "reason": assignment.reason
            }

            return Response({
                "status": True,
                "message": "Substitute teacher assignment details fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK)

        except SubstituteTeacherAssignment.DoesNotExist:
            return Response({
                "status": False,
                "message": "Substitute teacher assignment not found"
            }, status=status.HTTP_404_NOT_FOUND)

# ==========================================
# FINANCE MANAGEMENT APIs
# ==========================================

class FinanceDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_admission = StudentAcademicDetails.objects.count()

        total_amount_collected = StudentFinancialDetails.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0

        pending_amount = StudentFinancialDetails.objects.aggregate(
            total=Sum('balance_amount')
        )['total'] or 0

        return Response({
            'status': True,
            'data': {
                'total_admission': total_admission,
                'total_amount_collected': total_amount_collected,
                'pending_amount': pending_amount
            }
        }, status=status.HTTP_200_OK)


class AdmissionListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = StudentFinancialDetails.objects.select_related(
            'user'
        ).order_by('-id')
        
        queryset = queryset.filter(user__isnull=False)

        search = request.GET.get('search')
        admission_id = request.GET.get('admission_id')
        admission_date = request.GET.get('admission_date')

        if admission_id:
            queryset = queryset.filter(
                user__studentacademicdetails__admission_id__icontains=admission_id
            )

        if admission_date:
            queryset = queryset.filter(
                user__studentacademicdetails__admission_date=admission_date
            )

        if search:
            queryset = queryset.filter(
                Q(user__fullname__icontains=search) |
                Q(user__studentacademicdetails__admission_id__icontains=search)
            )

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size', 10))

        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AdmissionListSerializer(result_page, many=True)

        return paginator.get_paginated_response({
            'status': True,
            'data': serializer.data
        })


class AdmissionDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        try:
            student = Profiles.objects.select_related(
                'studentpersonaldetails',
                'studentacademicdetails',
                'studentfinancialdetails'
            ).get(pk=pk)

            print(
                "DETAIL STUDENT =",
                student.id,
                student.fullname
            )

            serializer = AdmissionDetailSerializer(student)

            return Response({
                'status': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Profiles.DoesNotExist:

            return Response({
                'status': False,
                'message': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)

class AdmissionUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_student(self, pk):
        try:
            return Profiles.objects.select_related(
                'studentpersonaldetails',
                'studentacademicdetails',
                'studentfinancialdetails'
            ).get(pk=pk)

        except Profiles.DoesNotExist:
            return None

    def put(self, request, pk):

        student = self.get_student(pk)

        if not student:
            return Response({
                'status': False,
                'message': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)

        print("UPDATE REQUEST DATA =", request.data)

        serializer = AdmissionUpdateSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            student.refresh_from_db()

            detail_serializer = AdmissionDetailSerializer(student)

            return Response({
                'status': True,
                'message': 'Admission updated successfully',
                'data': detail_serializer.data
            }, status=status.HTTP_200_OK)

        print("ERRORS =", serializer.errors)

        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)
    

class MultipleAdmissionDeleteAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request):

        serializer = MultipleAdmissionDeleteSerializer(data=request.data)

        if serializer.is_valid():

            ids = serializer.validated_data['ids']

            deleted_count = Profiles.objects.filter(
                id__in=ids
            ).delete()

            return Response({
                'status': True,
                'message': 'Admissions deleted successfully',
                'deleted_count': deleted_count[0]
            }, status=status.HTTP_200_OK)

        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    

# ==========================================
# FINANCE REPORT APIs
# ==========================================

class CourseReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        course_id = request.GET.get('course')

        courses = Course.objects.all().order_by('name')

        if course_id:
            courses = courses.filter(id=course_id)

        report_data = []

        for course in courses:

            academic_records = StudentAcademicDetails.objects.filter(
                courses=course
            )

            completed_students = academic_records.filter(
                status__iexact='Completed'
            ).count()

            batch = academic_records.first().batch if academic_records.exists() else None

            # Calculate duration from batch format like 2023-2026
            if batch and '-' in batch:
                try:
                    start_year, end_year = batch.split('-')
                    duration_years = int(end_year) - int(start_year)
                    duration = f"{duration_years} Year" if duration_years == 1 else f"{duration_years} Years"
                except Exception:
                    duration = 'N/A'
            else:
                duration = 'N/A'

            teacher_count = StaffManagementModel.objects.filter(
                student_class__batch=batch,
                is_teacher=True
            ).count() if batch else 0

            financial_records = StudentFinancialDetails.objects.filter(
                user__studentacademicdetails__courses=course
            )

            report_data.append({
                'course_id': course.id,
                'course_name': course.name,
                'total_students': academic_records.count(),
                'revenue_generated': financial_records.aggregate(
                    total=Sum('paid_amount')
                )['total'] or 0,
                'pending_fees': financial_records.aggregate(
                    total=Sum('balance_amount')
                )['total'] or 0,
                'batch': academic_records.first().batch if academic_records.exists() else None,
                'status': academic_records.first().status if academic_records.exists() else None,
                'duration': CourseReportSerializer.calculate_duration(batch),
                'completed_students': completed_students,
                'total_teachers': teacher_count

            })  

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size', 10))

        result_page = paginator.paginate_queryset(report_data, request)

        serializer = CourseReportSerializer(result_page, many=True)

        return paginator.get_paginated_response({
            'status': True,
            'data': serializer.data
        })


class StudentReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Profiles.objects.filter(
            role='Student'
        ).order_by('-id')

        search = request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(fullname__icontains=search) |
                Q(studentacademicdetails__admission_id__icontains=search)
            )

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size', 10))

        result_page = paginator.paginate_queryset(queryset, request)

        serializer = StudentReportSerializer(result_page, many=True)

        return paginator.get_paginated_response({
            'status': True,
            'data': serializer.data
        })

class TeacherReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = StaffManagementModel.objects.filter(
            is_teacher=True
        ).select_related(
            'profiles',
            'student_class'
        ).order_by('-id')

        search = request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(staff_name__icontains=search) |
                Q(profiles__user_id__icontains=search)
            )

        paginator = PageNumberPagination()
        paginator.page_size = int(
            request.GET.get('page_size', 10)
        )

        result_page = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = TeacherReportSerializer(
            result_page,
            many=True
        )

        return paginator.get_paginated_response({
            'status': True,
            'data': serializer.data
        })
    
class RevenueReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        year = request.GET.get('year')

        financial_queryset = StudentFinancialDetails.objects.all()
        staff_queryset = StaffManagementModel.objects.all()
        student_queryset = Profiles.objects.filter(role='Student')
        teacher_queryset = StaffManagementModel.objects.filter(
            is_teacher=True
        )

        year = request.GET.get('year')

        try:

            if year and year != "All Year":

                year = int(year)

                financial_queryset = financial_queryset.filter(
                    user__studentacademicdetails__admission_date__year=year
                )

                student_queryset = student_queryset.filter(
                    studentacademicdetails__admission_date__year=year
                )

        except ValueError:
            pass

        total_admission_revenue = financial_queryset.aggregate(
            total=Sum('admission_amount')
        )['total'] or 0

        total_fee_collection = financial_queryset.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0

        total_pending_amount = financial_queryset.aggregate(
            total=Sum('balance_amount')
        )['total'] or 0

        total_salary_expense = staff_queryset.aggregate(
            total=Sum('monthly_salary')
        )['total'] or 0

        total_students = student_queryset.count()

        total_teachers = teacher_queryset.count()

        active_students = student_queryset.filter(
            is_active=True
        ).count()

        active_teachers = teacher_queryset.filter(
            profiles__is_active=True
        ).count()

        return Response({
            'status': True,
            'data': {
                'total_admission_revenue': total_admission_revenue,
                'total_fee_collection': total_fee_collection,
                'total_pending_amount': total_pending_amount,
                'total_salary_expense': total_salary_expense,
                'total_students': total_students,
                'total_teachers': total_teachers,
                'active_students': active_students,
                'active_teachers': active_teachers
            }
        }, status=status.HTTP_200_OK)
    


