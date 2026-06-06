from django.urls import path
from .views import*

urlpatterns = [


#****************** staff management ***********************************************************
    path('staff-create/', AddStaffManagementView.as_view()),
    path('list-teaching-staff/', ListTeachingStaffAPIView.as_view()),
    path('list-non-teaching-staff/', ListNonTeachingStaffAPIView.as_view()),


    # Assigning scetion 
    path('todays-absent-teachers/', TodaysAbsentTeachersAPIView.as_view()),
    path('teacher-todays-timetable/<int:teacher_id>/', TeacherTodaysTimeTableAPIView.as_view()),
    path('available-teachers-list/', AvailableSubstituteTeachersAPIView.as_view()),
    path('assign-substitute-teacher/', AssignSubstituteTeacherAPIView.as_view()),
    path('list-substitute-teacher-assignments/', ListSubstituteTeacherAssignmentAPIView.as_view()),
    
    # path('kpi-cards-data/', SatffManagementKPICardsAPIView.as_view(), name='kpi-cards-data'),

# ***************************** academic management  *********************************************
    path('academic-kpi-cards/',AcademicManagementKPICardsAPIView.as_view()),
    path('add-class/' , AddListClassAPIView.as_view()),
    path('list-class/' , AddListClassAPIView.as_view()),
    path('edit-class/<int:class_id>/' , EditClassAPIView.as_view()),
    path('filterclass-by-batch/<str:batch>/' , FilterClassByBatchAPIView.as_view()),
    path('add-teacher-timetable/' , AddTeacherTimeTableAPIView.as_view()),
    path('list-teacher-timetable/<int:teacher_id>/' , ListTeacherTimeTableAPIView.as_view()),
    path('edit-teacher-timetable/<int:timetable_id>/' , EditTeacherTimeTableAPIView.as_view()),
    

#********************************* student management ************************************************** 
    path("dashboard/kpi/", StudentDashboardKPIAPIView.as_view()),
    path('add-student/' , AddStudents.as_view()),
    path('student-list/', StudentListAPIView.as_view(), name='student-list'),

    path("student-overview/<int:id>/",StudentoverviewAPIView.as_view()),
    path("student/edit/<int:profile_id>/",StudentEditAPIView.as_view()),
    path( "student-check-admission-id/", StudentCheckAdmissionIdAPIView.as_view()),
    



   

#********************************  finanace management **********************************************

   path('finance/dashboard/',FinanceDashboardAPIView.as_view(),name='finance-dashboard'),

    path('finance/admissions/',AdmissionListAPIView.as_view(),name='admission-list'),

    path('finance/admissions/<int:pk>/',AdmissionDetailAPIView.as_view(),name='admission-detail'),

    path('finance/admissions/<int:pk>/update/',AdmissionUpdateAPIView.as_view(),name='admission-update'),

    path('finance/admissions/delete/',MultipleAdmissionDeleteAPIView.as_view(),name='admission-delete'),

    path('finance/reports/courses/',CourseReportAPIView.as_view(),name='course-report'),

    path('finance/reports/students/',StudentReportAPIView.as_view(),name='student-report'),

    path('finance/reports/teachers/',TeacherReportAPIView.as_view(),name='teacher-report'),

    path('finance/reports/revenue/',RevenueReportAPIView.as_view(),name='revenue-report'),
]
