import re
from rest_framework import serializers
from superadmin_app.models import *


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField()
    category_id = serializers.IntegerField(required=False, allow_null=True)




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

            'status'

        ]

    def get_profile_photo(self, obj):

        try:

            if obj.photo:

                return obj.photo.url

        except Exception:

            pass

        return None

    def get_designation(self, obj):

        try:

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

        except Exception as e:

            print('DESIGNATION ERROR =', str(e))

            return None
    
    def get_department(self, obj):

        try:

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

        except Exception as e:

            print('DEPARTMENT ERROR =', str(e))

            return None

    def get_joining_date(self, obj):

        try:

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

        except Exception as e:

            print('JOINING DATE ERROR =', str(e))

        return None

    def get_assigned_by(self, obj):

        return "System / Founder "

    def get_status(self, obj):

        return (

            "Active"

            if obj.is_active

            else "Inactive"

        )

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
    

#Security Settings 


class LoginHistorySerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(
        source='user.user_id',
        read_only=True
    )

    fullname = serializers.CharField(
        source='user.fullname',
        read_only=True
    )

    role = serializers.CharField(
        source='user.role',
        read_only=True
    )

    email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:

        model = LoginHistory

        fields = [
            'id',
            'user_id',
            'fullname',
            'role',
            'email',
            'login_time',
            'logout_time',
            'ip_address',
            'device_name',
            'browser',
            'location',
            'login_status',
            'created_at'
        ]

        read_only_fields = fields

    def to_representation(self, instance):

            data = super().to_representation(instance)

            if data.get('device_name'):
                data['device_name'] = data['device_name'][:100]

            if data.get('ip_address') == '127.0.0.1':
                data['location'] = 'Local Development'

            return data

class ActiveSessionSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(
        source='user.user_id',
        read_only=True
    )

    fullname = serializers.CharField(
        source='user.fullname',
        read_only=True
    )

    role = serializers.CharField(
        source='user.role',
        read_only=True
    )

    def to_representation(self, instance):

        data = super().to_representation(instance)

        if data.get('device_name'):
            data['device_name'] = data['device_name'][:100]

        if data.get('ip_address') == '127.0.0.1':
            data['location'] = 'Local Development'

        return data

    class Meta:

        model = UserSession

        fields = [
            'id',
            'user_id',
            'fullname',
            'role',
            'device_name',
            'browser',
            'ip_address',
            'location',
            'is_active',
            'last_activity',
            'created_at'
        ]

        read_only_fields = fields


import secrets
import string


class PasswordResetSerializer(serializers.Serializer):

    user_id = serializers.CharField(
        required=True
    )

    send_email = serializers.BooleanField(
        default=True
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, attrs):

        user_id = attrs.get('user_id')

        if not user_id:
            raise serializers.ValidationError(
                'User ID is required.'
            )
        
        user = Profiles.objects.filter(
            user_id=user_id,
            is_active=True
        ).first()

        if not user:
            raise serializers.ValidationError(
                'User not found or inactive.'
            )
        
        if not user.email:
            raise serializers.ValidationError(
                'Selected user does not have a registered email address.'
            )

        return attrs

    def validate_user_id(
        self,
        value
    ):

        exists = Profiles.objects.filter(
            user_id=value,
            is_active=True
        ).exists()

        if not exists:

            raise serializers.ValidationError(
                "User not found."
            )

        return value
    
    def validate_remarks(self, value):

        if len(value.strip()) > 500:
            raise serializers.ValidationError(
                'Remarks cannot exceed 500 characters.'
            )
        return value.strip()

    def generate_password(self):

        alphabet = (
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits +
            '@#$%&!'
        )

        while True:

            password = ''.join(
                secrets.choice(alphabet)
                for _ in range(12)
            )

            if (
                any(c.isupper() for c in password)
                and any(c.islower() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in '@#$%&!' for c in password)
            ):
                return password
        
class PasswordResetAuditSerializer(serializers.ModelSerializer):

    target_user_id = serializers.CharField(
        source='target_user.user_id',
        read_only=True
    )

    target_user_name = serializers.CharField(
        source='target_user.fullname',
        read_only=True
    )

    reset_by_id = serializers.CharField(
        source='reset_by.user_id',
        read_only=True
    )

    reset_by_name = serializers.CharField(
        source='reset_by.fullname',
        read_only=True
    )

    class Meta:

        model = PasswordResetAudit

        fields = [
            'id',
            'target_user_id',
            'target_user_name',
            'reset_by_id',
            'reset_by_name',
            'temporary_password_sent',
            'remarks',
            'created_at'
        ]

        read_only_fields = fields

class SecurityDashboardSerializer(serializers.Serializer):

    total_logins = serializers.IntegerField()

    total_failed_logins = serializers.IntegerField()

    active_sessions = serializers.IntegerField()

    password_resets = serializers.IntegerField()

    def validate(self, attrs):

        for key, value in attrs.items():

            if value < 0:
                raise serializers.ValidationError(
                    f'{key} cannot be negative.'
                )

        return attrs


