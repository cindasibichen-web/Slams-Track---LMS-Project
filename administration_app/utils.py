from datetime import timedelta
from django.utils import timezone
from superadmin_app.models import *


def get_student_leave_details(student):
    """
    Returns absent attendance records for the last 6 months.
    """

    six_months_ago = timezone.now().date() - timedelta(days=180)

    absent_attendance = StudentAttendance.objects.filter(
        student=student,
        status="Absent",
        date__gte=six_months_ago
    ).order_by("-date")

    leave_details = [
        {
            "date": attendance.date,
            "reason": attendance.reason,
            "remarks": attendance.remarks
        }
        for attendance in absent_attendance
    ]

    return {
        "total_leave_days": absent_attendance.count(),
        "leave_details": leave_details
    }