from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from superadmin_app.utils.encrypt_decrypt_data import *
# from superadmin_app.utils.user_id_section import generate_user_id
from superadmin_app.manager import UserManager
import re
# Create your models here.
class Permission(models.Model):
    module = models.CharField(max_length=100,null=True, blank=True)  
    code = models.CharField(max_length=100,null=True, blank=True)   
    description = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.module} - {self.code}"

# category 
class Category(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)  
    description = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)  
    description = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# main profile model 
class Profiles(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('SuperAdmin', 'SuperAdmin'),
        ('Admin', 'Admin'),
        ('Administration staff', 'Administration staff'),
        ('Non-administration staff', 'Non-administration staff'),
        ('Teacher' , 'Teacher'), 
        ('Student' , 'Student'),   
    )

    user_id = models.CharField(max_length=600, unique=True,null=True,blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
  

    fullname = models.CharField(max_length=600,null=True,blank=True)

    email = models.EmailField(unique=True)
    phone_number = EncryptedCharField(max_length=600,null=True,blank=True)



    role = models.CharField(max_length=100, choices=ROLE_CHOICES, null=True, blank=True)


    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True
    )
    objects = UserManager()

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email']
    

    # def generate_user_id(self):

    #     role_prefix = {
    #         'SuperAdmin': 'SUP',
    #         'Admin': 'ADM',
    #         'Staff': 'STF',
    #         'Accountant': 'ACT',
    #         'Teacher': 'TCH',
    #         'Student': 'STD',
    #     }

    #     prefix = role_prefix.get(self.role, 'USR')

    #     # Get last created user with same prefix
    #     last_user = Profiles.objects.filter(
    #         user_id__startswith=prefix
    #     ).order_by('-id').first()

    #     if last_user and last_user.user_id:
    #         match = re.search(r'(\d+)$', last_user.user_id)

    #         if match:
    #             last_number = int(match.group(1))
    #             new_number = last_number + 1
    #         else:
    #             new_number = 1
    #     else:
    #         new_number = 1

    #     return f"{prefix}-{new_number:03d}"
    
    
    # def save(self, *args, **kwargs):

    #     if not self.user_id:
    #         self.user_id = self.generate_user_id()

    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id if self.user_id else self.fullname} - {self.email if self.email else 'No Email'}"
    

# otp verification model 
class OTPVerification(models.Model):

    PURPOSE_CHOICES = (
        ('forgot_password', 'Forgot Password'),
    )

    user = models.ForeignKey(
        'Profiles',
        on_delete=models.CASCADE,
        related_name='otp_records'
    )

    otp = models.CharField(max_length=6)

    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default='forgot_password'
    )

    is_used = models.BooleanField(default=False)

    attempts = models.PositiveIntegerField(default=0)

    max_attempts = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True
    )
    secret = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
    
# student details model 

# student management

class StudentPersonalDetails(models.Model):
    user = models.OneToOneField(Profiles, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    blood_group = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    father_phone_number = models.CharField(max_length=255, null=True, blank=True)
    father_occupation = models.CharField(max_length=255, null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    mother_phone_number = models.CharField(max_length=255, null=True, blank=True)
    mother_occupation = models.CharField(max_length=255, null=True, blank=True)
    
    


    def __str__(self):
        return f"{self.user.fullname if self.user.fullname else self.user.user_id} - Personal Details"


class StudentAcademicDetails(models.Model):
    user = models.OneToOneField(Profiles, on_delete=models.CASCADE)
    student_class = models.ForeignKey('ClassModel', on_delete=models.SET_NULL ,null=True, blank=True)  
    batch = models.CharField(max_length=100, null=True, blank=True)
    roll_number = models.CharField(max_length=100, null=True, blank=True)
    section = models.CharField(max_length=100, null=True, blank=True) 
    student_type = models.CharField(max_length=100, null=True, blank=True)
    admission_id = models.CharField(max_length=100, null=True, blank=True)
    # eg class 1 A or class 2 B etc.
    admission_date = models.DateField(null=True, blank=True)
    previous_institute = models.TextField(null=True, blank=True)
    previous_qualifications = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)  

    def __str__(self):
        return f"{self.user.fullname if self.user.fullname else self.user.user_id} - Academic Details"
    

class StudentFinancialDetails(models.Model):
    user = models.OneToOneField(Profiles, on_delete=models.CASCADE , null=True, blank=True)
    admission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    course_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)  # e.g., cash, card, online
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    installment_plan = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return f"{self.user.fullname if self.user.fullname else self.user.user_id} - Financial Details"


class StudentDocumentDetails(models.Model):
    user = models.OneToOneField(Profiles, on_delete=models.CASCADE)
    student_photo = models.ImageField(upload_to='student_documents/student_photos/', null=True, blank=True)
    birth_certificate = models.FileField(upload_to='student_documents/birth_certificates/', null=True, blank=True)
    previous_school_tc = models.FileField(upload_to='student_documents/previous_school_tcs/', null=True, blank=True)
    aadhar_card = models.FileField(upload_to='student_documents/aadhar_cards/', null=True, blank=True)
    parent_id_proof = models.FileField(upload_to='student_documents/parent_id_proofs/', null=True, blank=True)
    caste_certificate = models.FileField(upload_to='student_documents/caste_certificates/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.fullname if self.user.fullname else self.user.user_id} - Document Details"
    

# =========================
# staff management MODEL
# =========================

class StaffManagementModel(models.Model):

    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    # STAFF_ROLE_CHOICES = (
    #     ('Administration staff', 'Administration staff'),
    #     ('Non-administration staff', 'Non-administration staff'),
    # )

    # teacher_id = models.CharField(
    #     max_length=100,
    #     unique=True,
    #     null=True,
    #     blank=True
    # )

    profiles = models.OneToOneField(
        Profiles,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        null=True,
        blank=True
    )

    # Personal Information
    staff_name = models.CharField(max_length=255)

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)

    dob = models.DateField()

    photo = models.ImageField(
        upload_to='teacher_photos/',
        null=True,
        blank=True
    )

    address = models.TextField()

    # Professional Information
    qualification = models.CharField(max_length=255)

    experience_year = models.IntegerField(default=0)

    specialization = models.CharField(max_length=255)

    subject_expertise = models.CharField(max_length=255)

    joining_date = models.DateField()
    designation = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=100)  # e.g., Full-time, Part-time, Contract

    department = models.CharField(max_length=255)

    # Assignment Details
    # course = models.CharField(max_length=255)

    # batch = models.CharField(max_length=255)

    # section = models.CharField(max_length=255)

    # class_timing = models.CharField(max_length=100)

    reporting_admin = models.CharField(max_length=255)

    # Salary Details
    salary_type = models.CharField(max_length=100)

    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    bank_account = models.CharField(max_length=255)

    bank_name = models.CharField(max_length=255)

    ifsc_code = models.CharField(max_length=100)

    payroll_applicable = models.BooleanField(default=False)

    # Login Access
    # create_login_access = models.BooleanField(default=False)

    # role = models.CharField(max_length=100, default='Teacher')

    # username = models.CharField(max_length=255, null=True, blank=True)/

    # temporary_password = models.CharField(max_length=255, null=True, blank=True)

    notify_teacher = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    is_teacher = models.BooleanField(default=True)
    
    # staff_role = models.CharField(max_length=100, choices=STAFF_ROLE_CHOICES)


    def __str__(self):
        return f"{self.profiles.user_id} - {self.staff_name}"
    

# subject model
class Subject(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)  
    description = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# class model 
class ClassModel(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    class_id = models.CharField(max_length=100,null=True, blank=True)  
    class_name = models.CharField(max_length=100,null=True, blank=True)
    level = models.CharField(max_length=100,null=True, blank=True) 
    section = models.CharField(max_length=100,null=True, blank=True)
    class_teacher = models.ForeignKey(StaffManagementModel, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)  
    batch = models.CharField(max_length=255,null=True, blank=True)
    subject = models.ManyToManyField(Subject, blank=True)
    department = models.CharField(max_length=255,null=True, blank=True)
    branch = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_id}  - {self.class_name}"
    

class TeachersTimeTable(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(StaffManagementModel, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20)  # e.g., Monday, Tuesday
    period = models.CharField(max_length=20)  # e.g., Period 1, Period 2
    subject = models.CharField(max_length=255)
    class_assigned = models.ForeignKey(ClassModel, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher.staff_name} - {self.day_of_week} - period {self.period}"
    
# attendance marking model 
class StudentAttendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half day', 'Half day'),
    )
    students_class = models.ForeignKey(ClassModel, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey(Profiles, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)  # e.g., Present, Absent, Late
    remarks = models.TextField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    taken_by = models.ForeignKey(StaffManagementModel, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.fullname if self.student.fullname else self.student.user_id} - {self.date} - {self.status}"
    

class TeacherLeave(models.Model):

    LEAVE_TYPE_CHOICES = (
        ("Casual Leave", "Casual Leave"),
        ("Sick Leave", "Sick Leave"),
        ("Emergency Leave", "Emergency Leave"),
        ("Half Day Leave", "Half Day Leave"),
        ("Permission", "Permission"),
        ("Other", "Other"),
    )

    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )

    teacher = models.ForeignKey(
        StaffManagementModel,
        on_delete=models.CASCADE,
        related_name="teacher_leaves"
    )

    leave_type = models.CharField(
        max_length=50,
        choices=LEAVE_TYPE_CHOICES
    )

    date = models.DateField()

    from_date = models.DateField()

    to_date = models.DateField()

    no_of_days = models.PositiveIntegerField( null=True,
        blank=True)

    half_day_type = models.CharField(
        max_length=20,
        choices=(
            ("First Half", "First Half"),
            ("Second Half", "Second Half")
        ),
        null=True,
        blank=True
    )

    reason = models.TextField()

    reachable_contact_number = models.CharField(
        max_length=15
    )

    supporting_document = models.FileField(
        upload_to="leave_documents/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    
    SubstituteTeacher = models.CharField(
        max_length=120,
          null=True,
        blank=True
        
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher.staff_name} - {self.leave_type}"
    

# assign substitute teacher model
class SubstituteTeacherAssignment(models.Model):
    class_assigned = models.ForeignKey(ClassModel, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    original_teacher = models.ForeignKey(StaffManagementModel, on_delete=models.CASCADE, related_name='original_teacher_assignments')
    substitute_teacher = models.ForeignKey(StaffManagementModel, on_delete=models.CASCADE, related_name='substitute_teacher_assignments')
    date = models.DateField()
    period = models.CharField(max_length=20)  # e.g., Period 1, Period 2
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.class_assigned.class_name} - {self.subject} - {self.date} - {self.period}" 


# teachers attendance 
class TeacherstaffAttendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half day', 'Half day'),
    )
    teacher = models.ForeignKey(StaffManagementModel, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(choices=STATUS_CHOICES,max_length=20)  # e.g., Present, Absent, Late
    remarks = models.TextField(null=True, blank=True)
    checked_in_time = models.TimeField(null=True, blank=True)
    checked_out_time = models.TimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=True)


    class Meta:
        unique_together = ('teacher', 'date')

    def __str__(self):
        return f"{self.teacher.staff_name} - {self.date} - {self.status}"