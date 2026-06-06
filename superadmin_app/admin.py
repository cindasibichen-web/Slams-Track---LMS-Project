from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(Permission)
admin.site.register(Profiles)
admin.site.register(OTPVerification)
admin.site.register(StaffManagementModel)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(ClassModel)
admin.site.register(StudentPersonalDetails)
admin.site.register(StudentAcademicDetails)
admin.site.register(StudentFinancialDetails)
admin.site.register(StudentDocumentDetails)
admin.site.register(TeachersTimeTable)
admin.site.register(StudentAttendance)
admin.site.register(TeacherLeave)
admin.site.register(SubstituteTeacherAssignment)
admin.site.register(TeacherstaffAttendance)