from django.urls import path
from .views import *
urlpatterns = [
   

   path('login/', LoginAPIView.as_view()),
   path('list-categories/', ListCategoryAPIView.as_view()),
   path('forgot-password/', ForgotPasswordAPIView.as_view()),
   path('verify-otp/', VerifyOTPAPIView.as_view()),
   path( "forgot-password/resend-otp/",ResendForgotPasswordOTPAPIView.as_view()),
   path('reset-password/', ResetPasswordAPIView.as_view()),
   path('token-refresh/', TokenRefreshAPIView.as_view()),
   path('logout/', LogoutAPIView.as_view()),
   
   # path('check-login/', CheckLoginStateAPIView.as_view()),

   # path('assign-category/', AssignCategoryAPIView.as_view()),
  

   #****************************** dashboard section **************************** 

   path('dashboard-kpi-cards/', DashboardKpiCardsAPIViews.as_view()),

  path('dashboard-charts/' , DashboardStudentPieChartBatchCountAPIViews.as_view()),


   #********************* attendance management ************************************
   path('attendance-kpi-cards/', AttendanceManagementKPICardsAPIView.as_view()),
   path('teacher-attendance-list/', TeacherAttendanceListAPIView.as_view()),
   path('mark-teacher-attendance/', MarkTeachersAttendance.as_view()),
   path('students-attendance-list/', StudentAttendanceListAPIView.as_view()),
   path('mark-staff-attendance/', MarkStaffAttendanceAPIView.as_view()),

   path('staff-attendance-list/', StaffAttendanceListAPIView.as_view()),

   path('export-teachers-attendance/', ExportExcelTeachersAttendanceAPI.as_view()),
   path('export-students-attendance/', ExportStudentAttendanceExcelAPIView.as_view()),
   path('export-staff-attendance/', ExportStaffAttendanceExcelAPIView.as_view()),

   

   # ==========================

# PROFILE SETTINGS URLS

# ==========================

   path('settings/profile/',ProfileSettingsAPIView.as_view(),name='profile-settings'),

   path('settings/profile/update/',ProfileSettingsUpdateAPIView.as_view(),name='profile-settings-update'),

   path('settings/change-password/',ChangePasswordAPIView.as_view(),name='change-password'),

   path('settings/logout/',LogoutAPIView.as_view(),name='logout'),


]
