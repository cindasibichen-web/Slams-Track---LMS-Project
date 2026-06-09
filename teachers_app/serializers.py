from rest_framework import serializers
from superadmin_app.models import *
from django.utils import timezone


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

            today = timezone.now().date()

            total_students = StudentAcademicDetails.objects.filter(
                student_class=assigned_class
            ).count()

            attendance_qs = StudentAttendance.objects.filter(
                students_class=assigned_class,
                date=today
            )

            present_count = attendance_qs.filter(status="Present").count()
            absent_count = attendance_qs.filter(status="Absent").count()
            others_count = attendance_qs.exclude(status__in=["Present", "Absent"]).count()

            return {
                "id": assigned_class.id,
                "class_id": assigned_class.class_id,
                "class_name": assigned_class.class_name,
                "level": assigned_class.level,
                "section": assigned_class.section,
                "batch": assigned_class.batch,
                "department": assigned_class.department,
                "branch": assigned_class.branch,
                "status": assigned_class.status,
                "attendance_stats": {
                    "total_students": total_students,
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "others_count": others_count
                }
            }
    
# applyleave 

# applyleave 

class TeacherLeaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeacherLeave
        fields = "__all__"
        read_only_fields = ["teacher", "status"]

    def validate(self, attrs):

        leave_type = attrs.get("leave_type")
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")
        today = timezone.now().date()

        # Previous date validation
        if from_date < today:
            raise serializers.ValidationError(
                {"from_date": "Previous dates are not allowed."}
            )

        if to_date < today:
            raise serializers.ValidationError(
                {"to_date": "Previous dates are not allowed."}
            )

        # To date must be greater than or equal to from date
        if to_date < from_date:
            raise serializers.ValidationError(
                {"to_date": "To date must be greater than or equal to from date."}
            )

        # Use the teacher instance passed from the view context
        teacher = self.context.get("teacher")
        
        if not teacher:
            raise serializers.ValidationError("Teacher profile not found.")

        # Check overlapping leave applications
        existing_leave = TeacherLeave.objects.filter(
            teacher=teacher,
            from_date__lte=to_date,
            to_date__gte=from_date
        ).exists()

        if existing_leave:
            raise serializers.ValidationError(
                "You have already applied leave for the selected date(s)."
            )

        return attrs

    def create(self, validated_data):

        from_date = validated_data["from_date"]
        to_date = validated_data["to_date"]
        leave_type = validated_data["leave_type"]

        # Calculate no_of_days
        if leave_type == "Half Day Leave":
            validated_data["no_of_days"] = 1
        else:
            validated_data["no_of_days"] = (
                (to_date - from_date).days + 1
            )

        return super().create(validated_data)
class TeacherLeaveListSerializer(serializers.ModelSerializer):

 
    class Meta:
        model = TeacherLeave
        fields = [
            "id",
         
            "leave_type",
            "date",
            "from_date",
            "to_date",
            "no_of_days",
            "half_day_type",
            "reason",
            "reachable_contact_number",
            "supporting_document",
            "status",
              "SubstituteTeacher",
            "created_at",
        ]