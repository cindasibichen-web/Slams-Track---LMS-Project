from django.urls import path
from .views import*

urlpatterns = [

    path('staff-create/', AddStaffManagementView.as_view()),
    path('list-teaching-staff/', ListTeachingStaffAPIView.as_view()),
    path('list-non-teaching-staff/', ListNonTeachingStaffAPIView.as_view()),
    path('add-class/' , AddListClassAPIView.as_view()),
    path('list-class/' , AddListClassAPIView.as_view()),
    path('edit-class/<int:class_id>/' , EditClassAPIView.as_view()),
    path('filterclass-by-batch/<str:batch>/' , FilterClassByBatchAPIView.as_view()),

    path('add-teacher-timetable/' , AddTeacherTimeTableAPIView.as_view()),
    path('list-teacher-timetable/<int:teacher_id>/' , ListTeacherTimeTableAPIView.as_view()),
    path('edit-teacher-timetable/<int:timetable_id>/' , EditTeacherTimeTableAPIView.as_view()),

    path('add-student/' , AddStudents.as_view()),
path('student-list/', StudentListAPIView.as_view(), name='student-list'),

path("student-overview/<int:id>/",StudentoverviewAPIView.as_view(),name="student-overview"),
   
]
