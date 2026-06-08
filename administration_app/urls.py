from django.urls import path
from .views import*

urlpatterns = [

    path('staff-create/', AddStaffManagementView.as_view()),
    path('list-teaching-staff/', ListTeachingStaffAPIView.as_view()),
    path('list-non-teaching-staff/', ListNonTeachingStaffAPIView.as_view()),
    path('add-class/' , AddListClassAPIView.as_view()),
    path('add-student/' , AddListStudents.as_view()),

    path("finance-test/", finance_test, name="finance-test"),

    path('finance/dashboard/',FinanceDashboardAPIView.as_view(),name='finance-dashboard'),

    path('finance/admissions/',AdmissionListAPIView.as_view(),name='admission-list'),

    path('finance/admissions/<int:pk>/',AdmissionDetailAPIView.as_view(),name='admission-detail'),

    path('finance/admissions/<int:pk>/update/',AdmissionUpdateAPIView.as_view(),name='admission-update'),

    path('finance/admissions/delete/',MultipleAdmissionDeleteAPIView.as_view(),name='admission-delete'),

    path('finance/reports/courses/',CourseReportAPIView.as_view(),name='course-report'),

    path('finance/reports/students/',StudentReportAPIView.as_view(),name='student-report'),

    path('finance/reports/teachers/',TeacherReportAPIView.as_view(),name='teacher-report'),

    path('finance/reports/revenue/',RevenueReportAPIView.as_view(),name='revenue-report'),

    #Exports 

    path('finance/export/admissions/',AdmissionExportAPIView.as_view()),

    path('finance/export/students/',StudentReportExportAPIView.as_view()),

    path('finance/export/teachers/',TeacherReportExportAPIView.as_view()),

    path('finance/export/revenue/',RevenueReportExportAPIView.as_view()),


]
