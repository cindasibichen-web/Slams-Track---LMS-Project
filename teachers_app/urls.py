from django.urls import path
from .views import *

urlpatterns = [

path('teacher-profile/', TeacherProfileAPIView.as_view()),
path('timetable/', TeacherTimeTableGetAPIView.as_view()),
]
