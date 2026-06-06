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


    # settings profile 
# =====================================================
# PROFILE SETTINGS SERIALIZER
# =====================================================

class ProfileSettingsSerializer(serializers.ModelSerializer):

    profile_photo = serializers.SerializerMethodField()

    designation = serializers.SerializerMethodField()

    department = serializers.SerializerMethodField()

    joining_date = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    assigned_by = serializers.SerializerMethodField()

    employee_id = serializers.CharField(

        source='user_id',

        read_only=True

    )

    account_created = serializers.DateTimeField(

        source='date_joined',

        read_only=True

    )
    address = serializers.SerializerMethodField() 
    gender = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    


    class Meta:

        model = Profiles

        fields = [

            'profile_photo',

            'fullname',

            'role',

            'phone_number',

            'email',

            'address',

            'gender',

            'employee_id',

            'designation',

            'department',

            'joining_date',

            'assigned_by',

            'account_created',

            'status',

            'permissions'

        ]

    def get_permissions(self, obj):

        return list(
            obj.permissions.values_list(
                "code",
                flat=True
            )
        )

    def get_profile_photo(self, obj):

        try:

            if obj.photo:

                return obj.photo.url

        except Exception:

            pass

        return None

    def get_designation(self, obj):

        staff = getattr(

            obj,

            'teacher_profile',

            None

        )

        return (

            staff.designation

            if staff

            else None

        )

    def get_department(self, obj):

        staff = getattr(

            obj,

            'teacher_profile',

            None

        )

        return (

            staff.department

            if staff

            else None

        )

    def get_joining_date(self, obj):

        staff = getattr(

            obj,

            'teacher_profile',

            None

        )

        return (

            staff.joining_date

            if staff

            else None

        )

    def get_assigned_by(self, obj):

        return "System / Founder"

    def get_status(self, obj):

        return (

            "Active"

            if obj.is_active

            else "Inactive"

        )
    def get_address(self, obj):

        staff = getattr(

            obj,

            'user_profiles',

            None

        )


        return (staff.address


            if staff

            else None)
    
    def get_gender(self, obj):

        staff = getattr(

            obj,

            'user_profiles',

            None

        )


        return (staff.gender


            if staff

            else None)

# =====================================================
# PROFILE UPDATE SERIALIZER
# =====================================================

class ProfileSettingsUpdateSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(

        required=False

    )

    address = serializers.CharField(

        required=False,

        allow_blank=True

    )

    gender = serializers.CharField(

        required=False,

        allow_blank=True

    )

    profile_photo = serializers.ImageField(

        required=False,

        allow_null=True

    )

    class Meta:

        model = Profiles

        fields = [

            'fullname',

            'email',

            'phone_number',

            'address',

            'gender',

            'profile_photo'

        ]

    def validate_email(self, value):

        value = value.strip().lower()

        queryset = Profiles.objects.filter(
            email__iexact=value
        )

        if self.instance:

            queryset = queryset.exclude(

                pk=self.instance.pk

            )

        if queryset.exists():

            raise serializers.ValidationError(

                "Email already exists."

            )

        return value

    def validate_phone_number(

        self,

        value

    ):

        if not value:

            return value

        digits = ''.join(

            filter(

                str.isdigit,

                value

            )

        )

        value = digits

        if len(digits) != 10:

            raise serializers.ValidationError(

                "Phone number must contain exactly 10 digits."

            )

        queryset = Profiles.objects.filter(
            phone_number__iexact=value
        )

        if self.instance:

            queryset = queryset.exclude(

                pk=self.instance.pk

            )

        if queryset.exists():

            raise serializers.ValidationError(

                "Phone number already exists."

            )

        return value

    def validate_gender(

        self,

        value

    ):

        if not value:

            return value

        allowed = [

            "Male",

            "Female",

            "Other"

        ]

        if value not in allowed:

            raise serializers.ValidationError(

                f"Gender must be one of {allowed}"

            )

        return value

    def update(
        self,
        instance,
        validated_data
    ):


        if 'fullname' in validated_data:
            instance.fullname = validated_data.get('fullname') or ''

        if 'email' in validated_data:
            instance.email = validated_data.get('email') or ''

        if 'phone_number' in validated_data:
                    instance.phone_number = ''.join(
            filter(
                str.isdigit,
                validated_data.get('phone_number', '')
            )
        )

        if 'address' in validated_data:
            instance.address = validated_data.get('address') or ''

        if 'gender' in validated_data:
            instance.gender = validated_data.get('gender') or ''

        if 'profile_photo' in validated_data:
            instance.photo = validated_data.get('profile_photo')

        instance.save(
            update_fields=[
                'fullname',
                'email',
                'phone_number',
                'address',
                'gender',
                'photo'
            ]
        )

        instance.refresh_from_db()

        return instance

# =====================================================
# CHANGE PASSWORD SERIALIZER
# =====================================================

class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField(
        required=True,
        write_only=True
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True
    )

    confirm_password = serializers.CharField(
        required=True,
        write_only=True
    )

    def validate(self, attrs):

        current_password = attrs.get(
            'current_password'
        )

        new_password = attrs.get(
            'new_password'
        )

        confirm_password = attrs.get(
            'confirm_password'
        )

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password':
                'Passwords do not match.'
            })

        if current_password == new_password:
            raise serializers.ValidationError({
                'new_password':
                'New password cannot be same as current password.'
            })

        if len(new_password) < 8:
            raise serializers.ValidationError({
                'new_password':
                'Password must contain at least 8 characters.'
            })

        if not re.search(r'[A-Z]', new_password):
            raise serializers.ValidationError({
                'new_password':
                'Password must contain at least one uppercase letter.'
            })

        if not re.search(r'[a-z]', new_password):
            raise serializers.ValidationError({
                'new_password':
                'Password must contain at least one lowercase letter.'
            })

        if not re.search(r'\d', new_password):
            raise serializers.ValidationError({
                'new_password':
                'Password must contain at least one digit.'
            })

        if not re.search(
            r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>/?]',
            new_password
        ):
            raise serializers.ValidationError({
                'new_password':
                'Password must contain at least one special character.'
            })

        if "password" in new_password.lower():
            raise serializers.ValidationError({
                'new_password':
                'Password cannot contain the word password.'
            })

        return attrs