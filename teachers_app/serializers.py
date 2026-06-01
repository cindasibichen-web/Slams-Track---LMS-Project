from rest_framework import serializers
from superadmin_app.models import *


# teachers profile get serializer 
class TeacherProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='profiles.user_id', read_only=True)
    email = serializers.EmailField(source='profiles.email', read_only=True)
    phone_number = serializers.CharField(source='profiles.phone_number', read_only=True)
    role = serializers.CharField(source='profiles.role', read_only=True)
    category = serializers.CharField(
        source='profiles.category.name',
        read_only=True
    )
    assigned_class = serializers.SerializerMethodField()
    class Meta:
        model = StaffManagementModel
        fields = [
            'id',
            'user_id',
            'staff_name',
            'role',
            'category',
            'email',
            'phone_number',
            'photo',
            'gender',
            'dob' ,
            'address',
            'qualification',
            'subject_expertise',
            'joining_date',
            'designation',
            'employment_type',
            'department',
            # 'status',
            'monthly_salary',
            'bank_account',
            'bank_name',
            'ifsc_code',
            'payroll_applicable',
            
            'created_at',
            'assigned_class',
            # 'updated_at',
        


        ]

    def get_assigned_class(self, obj):

            assigned_class = ClassModel.objects.filter(
                class_teacher=obj
            ).first()

            if not assigned_class:
                return None

            return {
                "id": assigned_class.id,
                "class_id": assigned_class.class_id,
                "class_name": assigned_class.class_name,
                "level": assigned_class.level,
                "section": assigned_class.section,
                "batch": assigned_class.batch,
                "department": assigned_class.department,
                "branch": assigned_class.branch,
                "status": assigned_class.status
            }