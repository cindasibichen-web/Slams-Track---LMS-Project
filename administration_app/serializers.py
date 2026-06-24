from rest_framework import serializers
from superadmin_app.models import *
import random
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
import re
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
    @transaction.atomic
    def update(self, instance, validated_data):

        personal_data = validated_data.pop(
            "personal_details",
            {}
        )

        academic_data = validated_data.pop(
            "academic_details",
            {}
        )

        financial_data = validated_data.pop(
            "financial_details",
            {}
        )

        document_data = validated_data.pop(
            "document_details",
            {}
        )

        # Profile
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Personal
        personal, _ = StudentPersonalDetails.objects.get_or_create(
            user=instance
        )

        for attr, value in personal_data.items():
            setattr(personal, attr, value)

        personal.save()

        # Academic
        academic, _ = StudentAcademicDetails.objects.get_or_create(
            user=instance
        )

        for attr, value in academic_data.items():
            setattr(academic, attr, value)

        academic.save()

        # Financial
        financial, _ = StudentFinancialDetails.objects.get_or_create(
            user=instance
        )

        for attr, value in financial_data.items():
            setattr(financial, attr, value)

        financial.save()

        # Documents
        documents, _ = StudentDocumentDetails.objects.get_or_create(
            user=instance
        )

        for attr, value in document_data.items():
            setattr(documents, attr, value)

        documents.save()

        return instance


class StudentListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(
        source='user.id',
        read_only=True
    )
    student_id = serializers.CharField(source='user.user_id', read_only=True)
    fullname = serializers.CharField(source='user.fullname', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    class_name = serializers.CharField(source='student_class.class_name', read_only=True)

    section_roll = serializers.SerializerMethodField()
    fee_status = serializers.SerializerMethodField()
    attendance_status = serializers.SerializerMethodField()

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

            paid_amount = financial.paid_amount or 0
            balance_amount = financial.balance_amount or 0

            return "Paid" if paid_amount > 0 and balance_amount == 0 else "Pending"

        except StudentFinancialDetails.DoesNotExist:
            return "Pending"

    # -----------------------
    # ATTENDANCE STATUS (FIXED)
    # -----------------------
    def get_attendance_status(self, obj):
        attendance_map = self.context.get("attendance_map", {})

        return attendance_map.get(obj.user_id, "Not Marked")


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

    address = serializers.CharField(
        required=True,
        write_only=True
    )

    gender = serializers.CharField(
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

        address = validated_data.pop('address', None)

        gender = validated_data.pop('gender', None)


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
                address=address,
                gender=gender,
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
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
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
                address=address,
                gender=gender,
                category=request.user.category,
                is_active=False
            )

  
        # CREATE STAFF
   
        staff = StaffManagementModel.objects.create(
            profiles=profile_instance,
            address=address,
            gender=gender,
            **validated_data
        )

        return staff
    def update(self, instance, validated_data):

        permission_names = validated_data.pop("permissions", None)

        temporary_password = validated_data.pop(
            "temporary_password",
            None
        )

        email = validated_data.pop(
            "email",
            None
        )

        phone_number = validated_data.pop(
            "phone_number",
            None
        )

        role = validated_data.pop(
            "role",
            None
        )

        address = validated_data.pop(
            "address",
            None
        )

        gender = validated_data.pop(
            "gender",
            None
        )

        profile = instance.profiles

        # ----------------------------
        # UPDATE PROFILE
        # ----------------------------

        if email is not None:
            profile.email = email

        if phone_number is not None:
            profile.phone_number = phone_number

        if role is not None:
            profile.role = role

        if temporary_password:
            profile.password = make_password(
                temporary_password
            )
        if address is not None:
           instance.address = address

        if gender is not None:
              instance.gender = gender


        profile.save()

        # ----------------------------
        # UPDATE PERMISSIONS
        # ----------------------------

        if permission_names is not None:

            permission_objects = []

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

            profile.permissions.set(permission_objects)

        # ----------------------------
        # UPDATE STAFF DETAILS
        # ----------------------------

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
    
   # list staffs serializer
class ListStaffSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(source='profiles.user_id')
    email = serializers.EmailField(source='profiles.email')
    phone_number = serializers.CharField(source='profiles.phone_number')
    category = serializers.CharField(source='profiles.category.name')
    permissions = serializers.SlugRelatedField(
    source='profiles.permissions',
    many=True,
    read_only=True,
    slug_field='code'
)


    class Meta:
        model = StaffManagementModel
        fields = [
            'id',
            'user_id',
            'staff_name',
          
            'category',
            'photo' ,
            'is_teacher',
            'subject_expertise',
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
            'notify_teacher',
            'permissions',
              'is_block',
        ] 
    def get_permissions(self, obj):
        return list(
            obj.profiles.permissions.values_list('code', flat=True)
        )    


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
    subject_names = serializers.SerializerMethodField()

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
    def get_subject_names(self, obj):
        return list(
            obj.subject.values_list(
                "name",
                flat=True
            )
        )

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


# =============================================
# FINANCE SECTION SERIALIZERS
# =============================================
# =============================================
# FINANCE SECTION SERIALIZERS
# =============================================

class AdmissionListSerializer(serializers.ModelSerializer):

    # IMPORTANT:
    # Return Profile ID, not Financial ID
    id = serializers.IntegerField(
        source='user.id',
        read_only=True
    )

    student_name = serializers.SerializerMethodField()

    admission_id = serializers.CharField(
        source='user.studentacademicdetails.admission_id',
        read_only=True
    )

    admission_date = serializers.DateField(
        source='user.studentacademicdetails.admission_date',
        read_only=True
    )

    class_name = serializers.SerializerMethodField()

    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = StudentFinancialDetails

        fields = [
            'id',
            'admission_id',
            'student_name',
            'class_name',
            'admission_date',
            'admission_amount',
            'course_fee',
            'discount',
            'paid_amount',
            'balance_amount',
            'payment_mode',
            'payment_status'
        ]

    def get_student_name(self, obj):
        try:
            return obj.user.fullname if obj.user else ''
        except Exception:
            return ''

    def get_class_name(self, obj):
        try:
            academic = obj.user.studentacademicdetails

            if academic.student_class:
                return academic.student_class.class_name

            return None

        except Exception:
            return None

    def get_payment_status(self, obj):

        try:
            if float(obj.balance_amount or 0) <= 0:
                return "Paid"

            if float(obj.paid_amount or 0) > 0:
                return "Partial"

            return "Pending"

        except Exception:
            return "Pending"


class AdmissionDetailSerializer(serializers.ModelSerializer):

    personal_details = serializers.SerializerMethodField()
    academic_details = serializers.SerializerMethodField()
    financial_details = serializers.SerializerMethodField()
    document_details = serializers.SerializerMethodField()

    student_name = serializers.CharField(source='fullname', read_only=True)
    father_name = serializers.SerializerMethodField()
    mother_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    admission_id = serializers.SerializerMethodField()
    admission_date = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    admission_amount = serializers.SerializerMethodField()
    course_fee = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()
    payment_mode = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Profiles
        fields = [
                'id',
                'user_id',
                'fullname',
                'student_name',
                'father_name',
                'mother_name',
                'email',
                'phone_number',
                'course_name',
                'admission_id',
                'admission_date',
                'course',
                'gender',
                'admission_amount',
                'course_fee',
                'discount',
                'paid_amount',
                'balance_amount',
                'payment_mode',
                'payment_status',
                'personal_details',
                'academic_details',
                'financial_details',
                'document_details'
            ]
        read_only_fields = ['user_id','payment_mode','payment_status',]
        
    def get_admission_id(self, obj):
        try:
            return obj.studentacademicdetails.admission_id
        except Exception:
            return None

    def get_admission_date(self, obj):
        try:
            return obj.studentacademicdetails.admission_date
        except Exception:
            return None

    def get_course(self, obj):
        try:
            academic = obj.studentacademicdetails
            return academic.courses.name if academic.courses else None
        except Exception:
            return None
        
    def get_course_fee(self, obj):
        try:
            return obj.studentfinancialdetails.course_fee
        except Exception:
            return 0

    def get_discount(self, obj):
        try:
            return obj.studentfinancialdetails.discount
        except Exception:
            return 0

    def get_gender(self, obj):
        try:
            return obj.studentpersonaldetails.gender
        except Exception:
            return None

    def get_admission_amount(self, obj):
        try:
            return obj.studentfinancialdetails.admission_amount
        except Exception:
            return 0

    def get_paid_amount(self, obj):
        try:
            return obj.studentfinancialdetails.paid_amount
        except Exception:
            return 0

    def get_balance_amount(self, obj):
        try:
            return obj.studentfinancialdetails.balance_amount
        except Exception:
            return 0
    def get_payment_mode(self, obj):
        try:
            return obj.studentfinancialdetails.payment_mode
        except Exception:
            return None
    def get_payment_status(self, obj):
        try:
            financial = obj.studentfinancialdetails
            if financial.balance_amount <= 0:
                return 'Paid'
            elif financial.paid_amount > 0:
                return 'Partial'
            return 'Pending'
        except Exception:
            return None

    def get_course_name(self, obj):
        try:
            academic = obj.studentacademicdetails
            return academic.courses.name if academic.courses else None
        except Exception:
            return None
        
    def get_father_name(self, obj):
        try:
            return obj.studentpersonaldetails.parent_guardian_name
        except Exception:
            return None
        
    def get_mother_name(self, obj):
        try:
            personal = obj.studentpersonaldetails
            return getattr(personal, 'mother_name', None) or getattr(personal, 'mothers_name', None)
        except Exception:
           return None
        
    def get_personal_details(self, obj):
        try:
            data = StudentPersonalDetailsSerializer(
                obj.studentpersonaldetails
            ).data


            data['father_name'] = obj.studentpersonaldetails.parent_guardian_name
            data['parent_guardian_name'] = obj.studentpersonaldetails.parent_guardian_name

            data['mother_name'] = (
                getattr(obj.studentpersonaldetails, 'mother_name', None)
                or getattr(obj.studentpersonaldetails, 'mothers_name', None)
            )

            return data

        except Exception:
            return None

    def get_academic_details(self, obj):
        try:
            data = StudentAcademicDetailsSerializer(
                obj.studentacademicdetails
            ).data

            if obj.studentacademicdetails.courses:
                data['course_name'] = obj.studentacademicdetails.courses.name
            else:
                data['course_name'] = None

            return data
        except Exception:
            return None

    def get_financial_details(self, obj):
        try:
            return StudentFinancialDetailsSerializer(
                obj.studentfinancialdetails
            ).data
        except Exception:
            return None

    def get_document_details(self, obj):
        try:
            return StudentDocumentDetailsSerializer(
                obj.studentdocumentdetails
            ).data
        except Exception:
            return None

class AdmissionUpdateSerializer(serializers.ModelSerializer):

    personal_details = StudentPersonalDetailsSerializer(required=False)
    academic_details = StudentAcademicDetailsSerializer(required=False)
    financial_details = StudentFinancialDetailsSerializer(required=False)
    document_details = StudentDocumentDetailsSerializer(required=False)

    class Meta:

        model = Profiles

        fields = [
            'fullname',
            'email',
            'phone_number',
            'personal_details',
            'academic_details',
            'financial_details',
            'document_details'
        ]

    def validate(self, attrs):

        personal_data = attrs.get('personal_details')

        if personal_data:

            if 'father_name' in personal_data:

                personal_data['parent_guardian_name'] = (
                    personal_data.pop('father_name')
                )

        financial_data = attrs.get('financial_details')

        if financial_data:

            current_financial = None

            if self.instance:

                current_financial = (
                    StudentFinancialDetails.objects.filter(
                        user=self.instance
                    ).first()
                )

            admission_amount = Decimal(
                financial_data.get(
                    'admission_amount',
                    getattr(
                        current_financial,
                        'admission_amount',
                        0
                    )
                ) or 0
            )

            course_fee = Decimal(
                financial_data.get(
                    'course_fee',
                    getattr(
                        current_financial,
                        'course_fee',
                        0
                    )
                ) or 0
            )

            discount = Decimal(
                financial_data.get(
                    'discount',
                    getattr(
                        current_financial,
                        'discount',
                        0
                    )
                ) or 0
            )

            paid_amount = Decimal(
                financial_data.get(
                    'paid_amount',
                    getattr(
                        current_financial,
                        'paid_amount',
                        0
                    )
                ) or 0
            )

            total_payable = (
                admission_amount -
                discount +
                course_fee
            )

            if discount > admission_amount:

                raise serializers.ValidationError({
                    'discount':
                    'Discount cannot exceed admission amount.'
                })

            if paid_amount > total_payable:

                raise serializers.ValidationError({
                    'paid_amount':
                    'Paid amount cannot exceed total payable amount.'
                })

        return attrs

    def update(self, instance, validated_data):

        personal_data = validated_data.pop(
            'personal_details',
            None
        )

        academic_data = validated_data.pop(
            'academic_details',
            None
        )

        financial_data = validated_data.pop(
            'financial_details',
            None
        )

        document_data = validated_data.pop(
            'document_details',
            None
        )

        # PROFILE UPDATE

        for attr, value in validated_data.items():

            setattr(instance, attr, value)

        instance.save()

        # PERSONAL UPDATE

        if personal_data:

            personal, _ = (
                StudentPersonalDetails.objects.get_or_create(
                    user=instance
                )
            )

            if 'father_name' in personal_data:

                personal_data['parent_guardian_name'] = (
                    personal_data.pop('father_name')
                )

            for key, value in personal_data.items():

                setattr(personal, key, value)

            personal.save()

        # ACADEMIC UPDATE

        if academic_data:

            academic, _ = (
                StudentAcademicDetails.objects.get_or_create(
                    user=instance
                )
            )

            for key, value in academic_data.items():

                setattr(academic, key, value)

            academic.save()

        # FINANCIAL UPDATE

        if financial_data:

            financial, _ = (
                StudentFinancialDetails.objects.get_or_create(
                    user=instance
                )
            )

            for key, value in financial_data.items():

                setattr(financial, key, value)

            admission_amount = Decimal(
                financial.admission_amount or 0
            )

            course_fee = Decimal(
                financial.course_fee or 0
            )

            discount = Decimal(
                financial.discount or 0
            )

            paid_amount = Decimal(
                financial.paid_amount or 0
            )

            # ==================================
            # TOTAL AMOUNT CALCULATION
            # (Admission Amount - Discount)
            # + Course Fee
            # ==================================

            total_amount = (
                admission_amount -
                discount +
                course_fee
            )

            if total_amount < 0:
                total_amount = Decimal("0")

            financial.balance_amount = max(
                total_amount - paid_amount,
                Decimal("0")
            )

            financial.save()

        # DOCUMENT UPDATE

        if document_data:

            document, _ = (
                StudentDocumentDetails.objects.get_or_create(
                    user=instance
                )
            )

            for key, value in document_data.items():


                setattr(document, key, value)

            document.save()

        instance.refresh_from_db()

        return instance
        
class MultipleAdmissionDeleteSerializer(serializers.Serializer):

    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

# =============================================
# REPORT SECTION SERIALIZERS
# =============================================

class ClassReportSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    course_standard = serializers.CharField()
    duration = serializers.CharField()
    active_students = serializers.IntegerField()
    completed_students = serializers.IntegerField()
    revenue_generated = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    pending_fees = serializers.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    total_teachers = serializers.IntegerField()
    batch = serializers.CharField(
        allow_null=True,
        required=False
    )
    status = serializers.CharField(
        allow_null=True,
        required=False
    )

    @staticmethod
    def calculate_duration(batch):

        if batch and "-" in batch:
            try:
                start_year, end_year = batch.split("-")
                years = int(end_year) - int(start_year)

                return (
                    f"{years} Year"
                    if years == 1
                    else f"{years} Years"
                )

            except Exception:
                pass

        return "N/A"

class StudentReportSerializer(serializers.ModelSerializer):

    admission_id = serializers.CharField(
        source='studentacademicdetails.admission_id',
        read_only=True
    )

    class_name = serializers.SerializerMethodField()

    gender = serializers.SerializerMethodField()

    collected_fees = serializers.SerializerMethodField()

    batch = serializers.SerializerMethodField()

    parent_number = serializers.SerializerMethodField()

    attendance_percentage = serializers.SerializerMethodField()

    student_status = serializers.SerializerMethodField()

    section = serializers.SerializerMethodField()

    email = serializers.EmailField(read_only=True)

    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = Profiles
        fields = [
            'id',
            'user_id',
            'fullname',
            'email',
            'phone_number',
            'admission_id',
            'class_name',
            'section',
            'gender',
            'collected_fees',
            'attendance_percentage',
            'batch',
            'parent_number',
            'student_status'
        ]

    def get_class_name(self, obj):
        try:
            return obj.studentacademicdetails.student_class.class_name
        except Exception:
            return None

    def get_section(self, obj):
        try:
            return obj.studentacademicdetails.student_class.section
        except Exception:
            return None

    def get_gender(self, obj):
        try:
            return obj.studentpersonaldetails.gender
        except Exception:
            return None

    def get_collected_fees(self, obj):
        try:
            return obj.studentfinancialdetails.paid_amount
        except Exception:
            return 0

    def get_batch(self, obj):
        try:
            return obj.studentacademicdetails.batch
        except Exception:
            return None

    def get_parent_number(self, obj):
        try:
            return obj.studentpersonaldetails.parent_guardian_phone_number
        except Exception:
            return None

    def get_attendance_percentage(self, obj):
        return "N/A"

    def get_student_status(self, obj):
        try:
            return obj.studentacademicdetails.status
        except Exception:
            return None
              
class TeacherReportSerializer(serializers.ModelSerializer):

    teacher_id = serializers.CharField(
        source='profiles.user_id',
        read_only=True
    )

    teacher_name = serializers.CharField(
        source='staff_name',
        read_only=True
    )

    joined_date = serializers.DateField(
        source='joining_date',
        read_only=True
    )

    salary = serializers.DecimalField(
        source='monthly_salary',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    incharge_class = serializers.SerializerMethodField()

    incharge_classes = serializers.SerializerMethodField()

    teacher_number = serializers.CharField(
        source='profiles.phone_number',
        read_only=True
    )

    attendance_percentage = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    class Meta:
        model = StaffManagementModel
        fields = [
            'teacher_id',
            'teacher_name',
            'joined_date',
            'gender',
            'salary',
            'attendance_percentage',
            'incharge_class',
            'incharge_classes',
            'teacher_number',
            'status'
        ]

    def get_incharge_class(self, obj):

        class_obj = ClassModel.objects.filter(
            class_teacher=obj
        ).first()

        return class_obj.class_name if class_obj else None

    def get_incharge_classes(self, obj):

        classes = ClassModel.objects.filter(
            class_teacher=obj
        ).values_list(
            'class_name',
            flat=True
        )

        return list(classes)

    def get_attendance_percentage(self, obj):
        return "N/A"

    def get_status(self, obj):

        if obj.profiles:
            return "Active" if obj.profiles.is_active else "Inactive"

        return "Inactive"
    
# all teachers leave requests serializer 

class TeachersLeaveListSerializer(serializers.ModelSerializer):

    teacher_id = serializers.CharField(source='teacher.profiles.user_id', read_only=True)
    teacher_name = serializers.CharField(source='teacher.staff_name', read_only=True)
    department = serializers.CharField(source='teacher.department', read_only=True)
    designation = serializers.CharField(source='teacher.designation', read_only=True)

    class Meta:
        model = TeacherLeave
        fields = [
            'id',
            'teacher_id',
            'teacher_name',
            'department',
            'designation',
            'leave_type',
            'from_date',
            'to_date',
            'reason',
            'status',
            'created_at'
        ]
