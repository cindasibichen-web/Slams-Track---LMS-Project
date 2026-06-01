from rest_framework import serializers
from superadmin_app.models import *
import random
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings

# Student add serializer 
#-------------------------------------------------Student------------------------------------------------------------------------------------


# Student add serializer 
# Student add serializer 
class StudentPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPersonalDetails
        exclude = ['user']


class StudentAcademicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAcademicDetails
        exclude = ['user']


class StudentFinancialDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentFinancialDetails
        exclude = ['user']


class StudentDocumentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocumentDetails
        exclude = ['user']


class StudentCreateSerializer(serializers.ModelSerializer):

    personal_details = StudentPersonalDetailsSerializer(required=False)
    academic_details = StudentAcademicDetailsSerializer(required=False)
    financial_details = StudentFinancialDetailsSerializer(required=False)
    document_details = StudentDocumentDetailsSerializer(required=False)

    category = serializers.SerializerMethodField()

    class Meta:
        model = Profiles
        fields = [
            'id',
            'user_id',
            'fullname',
            'email',
            'phone_number',
            'category',
            'personal_details',
            'academic_details',
            'financial_details',
            'document_details',
        ]

    def get_category(self, obj):
        return {
            "id": obj.category.id,
            "name": obj.category.name
        } if obj.category else None

    def create(self, validated_data):

        personal_data = validated_data.pop('personal_details', {})
        academic_data = validated_data.pop('academic_details', {})
        financial_data = validated_data.pop('financial_details', {})
        document_data = validated_data.pop('document_details', {})

        request = self.context.get("request")
        logged_user = request.user

        student = Profiles.objects.create(
            role='Student',
            category=logged_user.category,  # Same category as logged-in user
            **validated_data
        )

        StudentPersonalDetails.objects.create(
            user=student,
            **personal_data
        )

        StudentAcademicDetails.objects.create(
            user=student,
            **academic_data
        )

        StudentFinancialDetails.objects.create(
            user=student,
            **financial_data
        )

        StudentDocumentDetails.objects.create(
            user=student,
            **document_data
        )

        return student


class StudentListSerializer(serializers.ModelSerializer):

    student_id = serializers.CharField(
        source='user.user_id',
        read_only=True
    )

    fullname = serializers.CharField(
        source='user.fullname',
        read_only=True
    )

    phone_number = serializers.CharField(
        source='user.phone_number',
        read_only=True
    )

    class_name = serializers.CharField(
        source='student_class.class_name',
        read_only=True
    )

    section_roll = serializers.SerializerMethodField()

    fee_status = serializers.SerializerMethodField()

    class Meta:
        model = StudentAcademicDetails
        fields = [
            'id',
            'student_id',
            'fullname',
            'phone_number',
            'class_name',
            'section_roll',
            'admission_date',
            'fee_status',
            'status',
        ]

    def get_section_roll(self, obj):
        return {
            "section": obj.section,
            "roll_no": obj.roll_number
        }

    def get_fee_status(self, obj):
        try:
            financial = StudentFinancialDetails.objects.get(
                user=obj.user
            )

            if financial.balance_amount == 0:
                return "Paid"

            return "Pending"

        except StudentFinancialDetails.DoesNotExist:
            return "Pending"


# staffs managhement section serializers
class StaffCreateSerializer(serializers.ModelSerializer):

    permissions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )

    temporary_password = serializers.CharField(
        required=False,
        write_only=True
    )

    user_id = serializers.CharField(
        required=False,
        write_only=True
    )

    role = serializers.ChoiceField(
    choices=Profiles.ROLE_CHOICES,
    required=False,
    write_only=True
)

    email = serializers.EmailField(
        required=True,
        write_only=True
    )

    phone_number = serializers.CharField(
        required=True,
        write_only=True
    )



    class Meta:
        model = StaffManagementModel
        fields = '__all__'
        extra_kwargs = {
            'profiles': {'required': False}
        }

    def create(self, validated_data):

        permission_names = validated_data.pop('permissions', [])

        temporary_password = validated_data.pop('temporary_password', None)

        payload_user_id = validated_data.pop('user_id', None)

        role = validated_data.pop('role', None)

        email = validated_data.pop('email', None)

        phone_number = validated_data.pop('phone_number', None)

        request = self.context.get('request')

        profile_instance = None

        # =========================================
        # ADMINISTRATION STAFF
        # =========================================
        if role == "Administration staff":

            if not payload_user_id:
                raise serializers.ValidationError({
                    "user_id": "user_id is required for administration staff"
                })

            if not temporary_password:
                raise serializers.ValidationError({
                    "temporary_password": "temporary_password is required"
                })

            # CHECK USER ID EXISTS
            if Profiles.objects.filter(user_id=payload_user_id).exists():
                raise serializers.ValidationError({
                    "user_id": "This user_id already exists"
                })

            profile_instance = Profiles.objects.create(
                user_id=payload_user_id,
                fullname=validated_data.get('staff_name'),
                email=email,
                phone_number=phone_number,
                role=role,
                category=request.user.category,
                password=make_password(temporary_password)
            )

            permission_objects = []

            # =========================================
            # CREATE / GET PERMISSIONS
            # =========================================
            for permission_name in permission_names:

                module_name = permission_name.split("_")[0]

                permission_obj, created = Permission.objects.get_or_create(
                    code=permission_name,
                    defaults={
                        "module": module_name.title(),
                        "description": permission_name
                    }
                )

                permission_objects.append(permission_obj)

            profile_instance.permissions.set(permission_objects)

            # =========================================
            # SEND LOGIN EMAIL
            # =========================================
            subject = "Your Staff Login Credentials"

            message = f"""
Hello {validated_data.get('staff_name')},

Your administration staff account has been created.

Login Details:

User ID: {payload_user_id}

Password: {temporary_password}

Please change your password after first login.
"""

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [validated_data.get('email')],
                fail_silently=False
            )

        # =========================================
        # NON ADMINISTRATION STAFF
        # =========================================
        else:

            auto_user_id = f"NSTAFF{random.randint(1000,9999)}"

            profile_instance = Profiles.objects.create(
                user_id=auto_user_id,
                fullname=validated_data.get('staff_name'),
                email=email,
                phone_number=phone_number,
                role=role,
                category=request.user.category,
                is_active=False
            )

  
        # CREATE STAFF
   
        staff = StaffManagementModel.objects.create(
            profiles=profile_instance,
            **validated_data
        )

        return staff
    
   # list staffs serializer
class ListStaffSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(source='profiles.user_id')
    email = serializers.EmailField(source='profiles.email')
    phone_number = serializers.CharField(source='profiles.phone_number')

    class Meta:
        model = StaffManagementModel
        fields = [
            'id',
            'user_id',
            'staff_name',
            'is_teacher',
            'gender',
            'dob',
            'address',
            'email',
            'phone_number',
            'qualification',
            'experience_year',
            'joining_date',
            'designation',
            'employment_type',
            'department',
            'salary_type',
            'monthly_salary',
            'bank_account',
            'bank_name',
            'ifsc_code',
            'payroll_applicable',
            'created_at',
            'notify_teacher'
        ] 


# edit staff serializer
class EditStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffManagementModel
        fields = '__all__'
        # extra_kwargs = {
        #     'profiles': {'required': False}
        # }



    # add class 
class AddListEditClassSerializer(serializers.ModelSerializer):

    subjects = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ClassModel
        fields = '__all__'

    def _get_subjects(self, subject_names):

        unique_subjects = []
        seen = set()

        for subject in subject_names:
            subject = subject.strip()

            if subject.lower() not in seen:
                seen.add(subject.lower())
                unique_subjects.append(subject)

        subject_objects = []

        for subject_name in unique_subjects:

            subject = Subject.objects.filter(
                name__iexact=subject_name
            ).first()

            if not subject:
                subject = Subject.objects.create(
                    name=subject_name
                )

            subject_objects.append(subject)

        return subject_objects

    def create(self, validated_data):

        subject_names = validated_data.pop('subjects', [])

        class_instance = ClassModel.objects.create(**validated_data)

        subjects = self._get_subjects(subject_names)

        class_instance.subject.set(subjects)

        return class_instance

    def update(self, instance, validated_data):

        subject_names = validated_data.pop('subjects', None)

        # Update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update subjects only if provided
        if subject_names is not None:

            subjects = self._get_subjects(subject_names)

            # Remove old subjects and assign new ones
            instance.subject.set(subjects)

        return instance
    
 # teachers timetable serializer 
class TeacherTimeTableSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeachersTimeTable
        fields = '__all__'   