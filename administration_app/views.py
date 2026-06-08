from re import search
from django.http import HttpResponse
from openpyxl import Workbook
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import request, request, status
from .serializers import *
from superadmin_app.models import *
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, Q
from rest_framework.pagination import PageNumberPagination

# Create your views here.



# Add students 
class AddListStudents(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Student created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)  

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)  
  
    

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

        staff_members = StaffManagementModel.objects.filter(is_teacher=True, category=request.user.category)

        serializer = ListStaffSerializer(staff_members, many=True)

        return Response({
            "status": True,
            "message": "Teaching staff members retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    

# list non teaching staff
class ListNonTeachingStaffAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        staff_members = StaffManagementModel.objects.filter(is_teacher=False, category=request.user.category)

        serializer = ListStaffSerializer(staff_members, many=True)

        return Response({
            "status": True,
            "message": "Non-teaching staff members retrieved successfully",
            "data": serializer.data 
            }, status=status.HTTP_200_OK)
    

# class add list api 
class AddListClassAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self , request):
        classes = ClassModel.objects.filter(category=request.user.category)

        data = []

        for class_instance in classes:
            data.append({
                "id": class_instance.id,
                "class_id": class_instance.class_id,
                "class_name": class_instance.class_name,
                "subjects": class_instance.subjects,
                "created_at": class_instance.created_at,
                "updated_at": class_instance.updated_at
            })

        return Response({
            "status": True,
            "classes": data
        }, status=status.HTTP_200_OK)
    


    def post(self, request):

        serializer = AddListClassSerializer(data=request.data)

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
    
from django.shortcuts import render

def finance_test(request):
    return render(request, "test.html")


#EXPORTS 

class AdmissionExportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        print("ADMISSION EXPORT HIT")

        wb = Workbook()
        ws = wb.active
        ws.title = "Admissions"

        ws.append([
            "Admission ID",
            "Student Name",
            "Email",
            "Course",
            "Admission Date",
            "Admission Amount",
            "Paid Amount",
            "Balance Amount",
            "Payment Mode",
            "Payment Status"
        ])

        queryset = StudentFinancialDetails.objects.select_related(
            'user'
        )

        for obj in queryset:

            try:
                academic = obj.user.studentacademicdetails
                course = (
                    academic.courses.name
                    if academic.courses else ''
                )
            except:
                academic = None
                course = ''

            payment_status = (
                "Paid"
                if obj.balance_amount <= 0
                else "Partial"
            )

            ws.append([
                academic.admission_id if academic else '',
                obj.user.fullname if obj.user else '',
                obj.user.email if obj.user else '',
                course,
                academic.admission_date if academic else '',
                obj.admission_amount,
                obj.paid_amount,
                obj.balance_amount,
                obj.payment_mode,
                payment_status
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = (
            'attachment; filename=admissions_report.xlsx'
        )

        wb.save(response)

        return response
    
class StudentReportExportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wb = Workbook()
        ws = wb.active
        ws.title = "Students"

        ws.append([
            "Admission ID",
            "Student Name",
            "Phone Number",
            "Parent Number",
            "Course",
            "Batch",
            "Gender",
            "Collected Fees",
            "Pending Fees",
            "Attendance Percentage",
            "Status"

        ])

        students = Profiles.objects.filter(
            role='Student'
        )

        for student in students:

            try:
                academic = student.studentacademicdetails
                admission_id = academic.admission_id
                course = academic.courses.name if academic.courses else ''
                batch = academic.batch
            except:
                admission_id = ''
                course = ''
                batch = ''

            try:
                personal = student.studentpersonaldetails

                gender = personal.gender
                parent_number = (
                    personal.parent_guardian_phone_number
                )
            except:
                gender = ''
                parent_number = ''

            try:
                financial = student.studentfinancialdetails

                collected_fees = financial.paid_amount
                pending_fees = financial.balance_amount
            except:
                collected_fees = 0
                pending_fees = 0

            # Replace later with actual attendance model
            attendance_percentage = 'N/A'

            ws.append([
                admission_id,
                student.fullname,
                student.phone_number,
                parent_number,
                course,
                batch,
                gender,
                collected_fees,
                pending_fees,
                attendance_percentage,
                (
                    "Active"
                    if student.is_active
                    else "Inactive"
                )
            ])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = (
            'attachment; filename=student_report.xlsx'
        )

        wb.save(response)

        return response
    
class TeacherReportExportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wb = Workbook()
        ws = wb.active
        ws.title = "Teachers"

        ws.append([
            "Teacher ID",
            "Teacher Name",
            "Email",
            "Phone Number",
            "Joining Date",
            "Designation",
            "Department",
            "Qualification",
            "Experience",
            "Incharge Class",
            "Salary",
            "Status"
        ])

        teachers = StaffManagementModel.objects.filter(
            is_teacher=True
        ).select_related('profiles')

        for teacher in teachers:

            ws.append([
                teacher.profiles.user_id
                if teacher.profiles else '',

                teacher.staff_name,

                teacher.profiles.email
                if teacher.profiles else '',

                teacher.profiles.phone_number
                if teacher.profiles else '',

                teacher.joining_date,

                teacher.designation,

                teacher.department,

                teacher.qualification,

                teacher.experience_year,

                teacher.student_class.class_name
                if teacher.student_class else '',

                teacher.monthly_salary,

                (
                    "Active"
                    if teacher.profiles
                    and teacher.profiles.is_active
                    else "Inactive"
                )
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = (
            'attachment; filename=teacher_report.xlsx'
        )

        wb.save(response)

        return response
    

class RevenueReportExportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wb = Workbook()
        ws = wb.active
        ws.title = "Revenue"

        total_admission_revenue = (
            StudentFinancialDetails.objects.aggregate(
                total=Sum('admission_amount')
            )['total'] or 0
        )

        total_fee_collection = (
            StudentFinancialDetails.objects.aggregate(
                total=Sum('paid_amount')
            )['total'] or 0
        )

        total_pending_amount = (
            StudentFinancialDetails.objects.aggregate(
                total=Sum('balance_amount')
            )['total'] or 0
        )

        total_salary_expense = (
            StaffManagementModel.objects.aggregate(
                total=Sum('monthly_salary')
            )['total'] or 0
        )

        total_students = Profiles.objects.filter(
            role='Student'
        ).count()

        total_teachers = StaffManagementModel.objects.filter(
            is_teacher=True
        ).count()

        active_students = Profiles.objects.filter(
            role='Student',
            is_active=True
        ).count()

        active_teachers = StaffManagementModel.objects.filter(
            is_teacher=True,
            profiles__is_active=True
        ).count()

        net_profit = (
            total_fee_collection -
            total_salary_expense
        )

        ws.append(["Metric", "Amount"])

        ws.append([
            "Total Admission Revenue",
            total_admission_revenue
        ])

        ws.append([
            "Total Fee Collection",
            total_fee_collection
        ])

        ws.append([
            "Total Pending Amount",
            total_pending_amount
        ])

        ws.append([
            "Total Salary Expense",
            total_salary_expense
        ])

        ws.append([
            "Net Profit",
            net_profit
        ])

        ws.append([
            "Total Students",
            total_students
        ])

        ws.append([
            "Total Teachers",
            total_teachers
        ])

        ws.append([
            "Active Students",
            active_students
        ])

        ws.append([
            "Active Teachers",
            active_teachers
        ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = (
            'attachment; filename=revenue_report.xlsx'
        )

        wb.save(response)

        return response
    
