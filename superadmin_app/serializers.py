from rest_framework import serializers
from superadmin_app.models import *




class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField()
    category_id = serializers.IntegerField(required=False, allow_null=True)

    # category assigning serializer


# class AssignCategorySerializer(serializers.Serializer):

#     category_id = serializers.IntegerField()

class MarkTeachersAttendanceSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=["Present", "Absent", "Late", "Half day"]
    )
    remarks = serializers.CharField(required=False, allow_blank=True)
    checked_in_time = serializers.TimeField(
        required=False,
        allow_null=True,
        input_formats=["%H:%M", "%H:%M:%S"]
    )
    checked_out_time = serializers.TimeField(
        required=False,
        allow_null=True,
        input_formats=["%H:%M", "%H:%M:%S"]
    )


# mark staffs attendance serializer
class MarkStaffAttendanceSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=["Present", "Absent", "Late", "Half day"]
    )
    remarks = serializers.CharField(required=False, allow_blank=True)
    checked_in_time = serializers.TimeField(
        required=False,
        allow_null=True,
        input_formats=["%H:%M", "%H:%M:%S"]
    )
    checked_out_time = serializers.TimeField(
        required=False,
        allow_null=True,
        input_formats=["%H:%M", "%H:%M:%S"]
    )