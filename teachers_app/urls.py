from django.urls import path
from .views import *

urlpatterns = [


path("teacher-change-password/",TeacherChangePasswordAPIView.as_view()),
path('teacher-profile/', TeacherProfileAPIView.as_view()),
path('timetable/', TeacherTimeTableGetAPIView.as_view()),
path('list-classes-for-attendance/', TeacherClassListAPIView.as_view()),
path('class-students-attendance/', StudentAttendanceListAPIView.as_view()),
path('mark-attendance/', MarkAttendanceAPIView.as_view()),
path('class-attendance-history/', ClassAttendanceHistoryAPIView.as_view()),



path("teacher-apply-leave/", ApplyTeacherLeaveAPIView.as_view(),name="apply-leave"),
path( "teacher-leave-list/",TeacherLeaveListAPIView.as_view(),name="teacher-leave-list"),



]
