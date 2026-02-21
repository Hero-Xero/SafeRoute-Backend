from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser

# ==========================================
# 1. USERS & PROFILES
# ==========================================

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PARENT = 'PARENT', 'Parent'
        DRIVER = 'DRIVER', 'Driver'
        ASSISTANT = 'ASSISTANT', 'Assistant'

    role = models.CharField(max_length=15, choices=Role.choices, default=Role.PARENT)

    def __str__(self):
        return f"{self.username} ({self.role})"

class GuardianProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guardian_profile')
    phone_number = models.CharField(max_length=20)
    # Replaced strict address with notes since we use pin drops
    location_notes = models.TextField(blank=True, null=True, help_text="e.g., Yellow building, 3rd gate")

    def __str__(self):
        return f"Guardian: {self.user.username}"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Staff: {self.user.username}"


class PickupLocation(models.Model):
    # The parent who created this pin drop
    guardian = models.ForeignKey(GuardianProfile, on_delete=models.CASCADE, related_name='saved_locations')
    
    name = models.CharField(max_length=50, help_text="e.g., Home, Grandma's, Work")
    # Moved the PostGIS field here!
    coordinates = models.PointField(srid=4326, help_text="Exact GPS coordinates from pin drop")
    location_notes = models.TextField(blank=True, null=True, help_text="e.g., Yellow building, 3rd gate")

    def __str__(self):
        return f"{self.name} ({self.guardian.user.username})"

class Student(models.Model):
    guardian = models.ForeignKey(GuardianProfile, on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    default_pickup_location = models.ForeignKey(
        PickupLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='pickup_students'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Bus(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    capacity = models.IntegerField()

    def __str__(self):
        return self.plate_number

# ------------------------------------------
class PlannedRoute(models.Model):
    class Direction(models.TextChoices):
        TO_SCHOOL = 'TO_SCHOOL', 'To School'
        FROM_SCHOOL = 'FROM_SCHOOL', 'From School'
    
    name = models.CharField(max_length=100) # e.g., "Zamalek Morning Run"
    direction = models.CharField(max_length=20, choices=Direction.choices)
    
    # POSTGIS: The physical line drawn on the map
    path_polyline = models.LineStringField(srid=4326, blank=True, null=True)

    def __str__(self):
        return self.name

class PlannedStop(models.Model):
    planned_route = models.ForeignKey(PlannedRoute, on_delete=models.CASCADE, related_name='stops')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    order_index = models.PositiveIntegerField(help_text="1 for first stop, 2 for second...")
    estimated_time = models.TimeField()
    
    # POSTGIS: The designated pickup/dropoff point
    stop_location = models.PointField(srid=4326)

    class Meta:
        ordering = ['order_index'] 

    def __str__(self):
        return f"{self.planned_route.name} - Stop {self.order_index} ({self.student.first_name})"


# -------------------------------------------

class Trip(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
    
    planned_route = models.ForeignKey(PlannedRoute, on_delete=models.PROTECT)
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT)
    
    # The "Sick Day" fix: Driver required, Assistant optional
    driver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='driven_trips', limit_choices_to={'role': 'DRIVER'})
    assistant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assisted_trips', limit_choices_to={'role': 'ASSISTANT'})
    
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    def __str__(self):
        return f"{self.planned_route.name} | {self.date}"

class ActualStop(models.Model):
    class Status(models.TextChoices):
        BOARDED = 'BOARDED', 'Boarded'
        DROPPED_OFF = 'DROPPED_OFF', 'Dropped Off'
        ABSENT = 'ABSENT', 'Absent'
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='actual_stops')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=Status.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # POSTGIS: Where the bus *actually* was when the button was tapped
    actual_location = models.PointField(srid=4326, blank=True, null=True)

    def __str__(self):
        return f"{self.student.first_name} - {self.status}"