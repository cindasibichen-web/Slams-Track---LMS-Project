from rest_framework import serializers
from superadmin_app.models import *
import random
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from decimal import Decimal


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

    def validate(self, attrs):
        academic_data = attrs.get("academic_details", {})
        roll_number = academic_data.get("roll_number")

        # If roll number manually entered → check uniqueness
        if roll_number:
            exists = StudentAcademicDetails.objects.filter(
                roll_number=roll_number
            ).exists()

            if exists:
                raise serializers.ValidationError({
                    "roll_number": "This roll number already exists."
                })

        return attrs

    def get_next_roll_number(self):
        """
        Auto-generate next roll number based on numeric max value
        Example: 1, 2, 3 → next = 4
        """
        last = StudentAcademicDetails.objects.filter(
            roll_number__isnull=False
        ).exclude(roll_number="").order_by("-id").first()

        if not last or not last.roll_number:
            return "1"

        match = re.search(r'(\d+)$', str(last.roll_number))
        if match:
            return str(int(match.group(1)) + 1)

        return "1"

    @transaction.atomic
    def create(self, validated_data):

        personal_data = validated_data.pop('personal_details', {})
        academic_data = validated_data.pop('academic_details', {})
        financial_data = validated_data.pop('financial_details', {})
        document_data = validated_data.pop('document_details', {})

        request = self.context.get("request")
        logged_user = request.user

        # -------------------------------
        # HANDLE ROLL NUMBER LOGIC
        # -------------------------------
        roll_number = academic_data.get("roll_number")

        if not roll_number:
            roll_number = self.get_next_roll_number()

        academic_data["roll_number"] = roll_number

        # -------------------------------
        # GENERATE USER ID
        # -------------------------------
        last_student = Profiles.objects.filter(
            role="Student",
            user_id__startswith="STD"
        ).order_by("-id").first()

        if last_student and last_student.user_id:
            match = re.search(r'(\d+)$', last_student.user_id)
            next_number = int(match.group(1)) + 1 if match else 1
        else:
            next_number = 1

        user_id = f"STD{next_number:03d}"

        # -------------------------------
        # CREATE STUDENT PROFILE
        # -------------------------------
        student = Profiles.objects.create(
            user_id=user_id,
            role='Student',
            category=logged_user.category,
            **validated_data
        )

        # -------------------------------
        # CREATE RELATED TABLES
        # -------------------------------
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

    student_id = serializers.CharField(source='user.user_id', read_only=True)
    fullname = serializers.CharField(source='user.fullname', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    class_name = serializers.CharField(source='student_class.class_name', read_only=True)

    section_roll = serializers.SerializerMethodField()
    fee_status = serializers.SerializerMethodField()
    attendance_status = serializers.SerializerMethodField()
    attendance_date = serializers.SerializerMethodField()

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
            'attendance_date',
            'attendance_status',
            'status'
        ]

    # -----------------------
    # SECTION + ROLL
    # -----------------------
    def get_section_roll(self, obj):
        return {
            "section": obj.section,
            "roll_no": obj.roll_number
        }

    # -----------------------
    # FEE STATUS
    # -----------------------
    def get_fee_status(self, obj):
        try:
            financial = StudentFinancialDetails.objects.get(user=obj.user)

            paid_amount = financial.paid_amount or Decimal('0.00')
            balance_amount = financial.balance_amount or Decimal('0.00')

            if paid_amount > 0 and balance_amount == 0:
                return "Paid"

            return "Pending"

        except StudentFinancialDetails.DoesNotExist:
            return "Pending"

    # -----------------------
    # ATTENDANCE STATUS (DATE FILTERED)
    # -----------------------
    def get_attendance_status(self, obj):

        attendance_date = self.context.get('attendance_date')

        attendance = StudentAttendance.objects.filter(
            student=obj.user,
            date=attendance_date
        ).first()

        return attendance.status if attendance else "Not Marked"

    # -----------------------
    # ATTENDANCE DATE
    # -----------------------
    def get_attendance_date(self, obj):

        attendance_date = self.context.get('attendance_date')

        attendance = StudentAttendance.objects.filter(
            student=obj.user,
            date=attendance_date
        ).first()

        return attendance.date if attendance else None
        


class StudentEditSerializer(serializers.Serializer):

    # Profile
    fullname = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)

    # Personal
    dob = serializers.DateField(required=False)
    gender = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    blood_group = serializers.CharField(required=False)
    father_name = serializers.CharField(required=False)
    father_phone_number = serializers.CharField(required=False)
    father_occupation = serializers.CharField(required=False)
    mother_name = serializers.CharField(required=False)
    mother_phone_number = serializers.CharField(required=False)
    mother_occupation = serializers.CharField(required=False)

    # Academic
    student_class = serializers.IntegerField(required=False)
    batch = serializers.CharField(required=False)
    roll_number = serializers.CharField(required=False)
    section = serializers.CharField(required=False)
    student_type = serializers.CharField(required=False)
    admission_id = serializers.CharField(required=False)
    admission_date = serializers.DateField(required=False)
    previous_institute = serializers.CharField(required=False)
    previous_qualifications = serializers.CharField(required=False)
    status = serializers.CharField(required=False)

    # Financial
    admission_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    course_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    paid_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    payment_mode = serializers.CharField(required=False)
    balance_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    installment_plan = serializers.CharField(required=False)

    # Documents
    student_photo = serializers.ImageField(required=False)
    birth_certificate = serializers.FileField(required=False)
    previous_school_tc = serializers.FileField(required=False)
    aadhar_card = serializers.FileField(required=False)
    parent_id_proof = serializers.FileField(required=False)
    caste_certificate = serializers.FileField(required=False)


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
            'photo' ,
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