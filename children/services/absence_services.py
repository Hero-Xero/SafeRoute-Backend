from django.db import transaction
from django.utils import timezone
from children.models import StudentAbsence, Child
from trips.models import TripChild
from trips.enums import TripChildStatusChoices

def mark_students_absent(guardian, student_ids, date, notes=None):
    """
    Marks multiple students as absent for a specific date.
    Returns a list of created Absence objects.
    """
    absences = []
    # Ensure students belong to the guardian
    students = Child.objects.filter(id__in=student_ids, guardian=guardian)
    
    with transaction.atomic():
        for student in students:
            absence, created = StudentAbsence.objects.update_or_create(
                student=student,
                date=date,
                defaults={'notes': notes}
            )
            absences.append(absence)
            
            # If there's an active or scheduled trip for this student on this date, update status
            TripChild.objects.filter(
                child=student,
                trip__scheduled_date=date
            ).update(status=TripChildStatusChoices.ABSENT)
            
    return absences

def remove_students_absence(guardian, student_ids, date):
    """
    Removes absence marks for students on a specific date.
    """
    # Ensure students belong to the guardian
    students = Child.objects.filter(id__in=student_ids, guardian=guardian)
    
    with transaction.atomic():
        StudentAbsence.objects.filter(student__in=students, date=date).delete()
        
        # Optionally reset TripChild status to WAITING if trip is scheduled
        TripChild.objects.filter(
            child__in=students,
            trip__scheduled_date=date,
            status=TripChildStatusChoices.ABSENT
        ).update(status=TripChildStatusChoices.WAITING)
