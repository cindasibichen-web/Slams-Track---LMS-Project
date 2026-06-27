from django.urls import path
from .views import*

urlpatterns = [


#***************************************** staff management *******************************************************
    path('staff-kpi-cards-data/', StaffManagementKPICards.as_view(), name='kpi-cards-data'),
    path('staff-create/', AddStaffManagementView.as_view()),
    path('list-teaching-staff/', ListTeachingStaffAPIView.as_view()),
    path('edit-staff/<int:staff_id>/', EditStaffAPIView.as_view()),
    path('list-non-teaching-staff/', ListNonTeachingStaffAPIView.as_view()),

    path('staff/block-status/<int:staff_id>/',StaffBlockStatusAPIView.as_view(),  name='staff-block-status'),
 # Assigning scetion 
    path('todays-absent-teachers/', TodaysAbsentTeachersAPIView.as_view()),
    path('teacher-todays-timetable/<int:teacher_id>/', TeacherTodaysTimeTableAPIView.as_view()),
    path('available-teachers-list/', AvailableSubstituteTeachersAPIView.as_view()),
    path('assign-substitute-teacher/', AssignSubstituteTeacherAPIView.as_view()),
    path('list-substitute-teacher-assignments/', ListSubstituteTeacherAssignmentAPIView.as_view()),

    path('all-teachers-leave-list/', ListAllTeachersLeaveRequests.as_view()),
    
    path('approve-reject-leave-requets/',ApproveRejectTeachersLeaveRequests.as_view()),
    # path('reject-leave-requets/',RejectTeachersLeaveRequests.as_view()),
    path('leave-details-api/',LeaveDetailsAPIView.as_view()),

    
#***************************************** academic management  ****************************************************
    path('academic-kpi-cards/',AcademicManagementKPICardsAPIView.as_view()),
    path('add-class/' , AddListClassAPIView.as_view()),
    path('list-class/' , AddListClassAPIView.as_view()),
    path('edit-class/<int:class_id>/' , EditClassAPIView.as_view()),
    path('filterclass-by-batch/<str:batch>/' , FilterClassByBatchAPIView.as_view()),
    path('classes/sections/',ClassSectionsAPIView.as_view()),
    path('add-teacher-timetable/' , AddTeacherTimeTableAPIView.as_view()),
    path('list-teacher-timetable/<int:teacher_id>/' , ListTeacherTimeTableAPIView.as_view()),
    path('edit-teacher-timetable/<int:timetable_id>/' , EditTeacherTimeTableAPIView.as_view()),

    path('delete-time-table/<int:time_table_id>/',DeleteTeachersTimeTable.as_view()),

    path('get-class-details-by-id/<int:class_id>/' , ClassDetailsById.as_view()),

    path('departments/',DepartmentListAPIView.as_view(),name='department-list'),
    
#******************************************* student management ******************************************************

    path("dashboard/kpi/", StudentDashboardKPIAPIView.as_view()),
    path('add-student/' , AddStudents.as_view()),
    path('student-list/', StudentListAPIView.as_view(), name='student-list'),
    path('arrange-roll-numbers/',ArrangeRollNumbersAPIView.as_view(),name='arrange-roll-numbers'),

    path("student-overview/<int:id>/",StudentoverviewAPIView.as_view()),
    path("student/edit/<int:profile_id>/",StudentEditAPIView.as_view()),
    path( "student-check-admission-id/", StudentCheckAdmissionIdAPIView.as_view()),

    path('list-classes-for-dropdowns/',ListClassesForDropDowns.as_view()) ,
    path('sections-drop/',SectionsdropAPIView.as_view(), name='class-sections'),
    

#****************************************** finanace management ******************************************************

   path('finance/dashboard/',FinanceDashboardAPIView.as_view(),name='finance-dashboard'),
   path('finance/admissions/',AdmissionListAPIView.as_view(),name='admission-list'),
   path('finance/admissions/<int:pk>/',AdmissionDetailAPIView.as_view(),name='admission-detail'),
   path('finance/admissions/<int:pk>/update/',AdmissionUpdateAPIView.as_view(),name='admission-update'),
   path('finance/admissions/delete/',MultipleAdmissionDeleteAPIView.as_view(),name='admission-delete'),
   path('finance/reports/courses/',CourseReportAPIView.as_view(),name='course-report'),
   path('finance/reports/students/',StudentReportAPIView.as_view(),name='student-report'),
   path('finance/reports/teachers/',TeacherReportAPIView.as_view(),name='teacher-report'),
   path('finance/reports/revenue-years/',RevenueYearListAPIView.as_view(),name='revenue-years'),
    path('finance/reports/revenue-months/',RevenueMonthListAPIView.as_view(),name='revenue-months'),
   path('finance/reports/revenue/',RevenueReportAPIView.as_view(),name='revenue-report'),

# ******************************************* exports ***************************************************************** 

    path('finance/export/admissions/',AdmissionExportAPIView.as_view()),

    path('finance/export/students/',StudentReportExportAPIView.as_view()),

    path('finance/export/teachers/',TeacherReportExportAPIView.as_view()),

    path('finance/export/revenue/',RevenueReportExportAPIView.as_view())




]
