from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from users.models import AdminUser, DriverUser, AssistantUser, GuardianUser
from children.models import Child, StudentSavedLocation, LocationChangeRequest
from children.enums import LocationChangeStatus, LocationChangeType
from trips.models import Bus, Route, RouteStop, RouteChild, Trip, TripChild
from trips.enums import TripTypeChoices, TripStatusChoices, TripChildStatusChoices, BusStatusChoices

class Command(BaseCommand):
    help = 'Generates extensive dummy data for testing the SafeRoute system.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating dummy data...')

        with transaction.atomic():
            # ---------------------------------------------------------
            # 1. Create Core Staff Accounts
            # ---------------------------------------------------------
            admin, _ = AdminUser.objects.get_or_create(
                email='admin@saferoute.com',
                defaults={
                    'first_name': 'Super', 'last_name': 'Admin',
                    'phone_number': '+1234567890',
                    'is_staff': True, 'is_superuser': True, 'is_verified': True
                }
            )
            admin.set_password('Admin123!')
            admin.save()

            driver_1, _ = DriverUser.objects.get_or_create(
                email='driver1@saferoute.com',
                defaults={'first_name': 'John', 'last_name': 'Driver', 'phone_number': '+1234567891', 'is_verified': True}
            )
            driver_1.set_password('Driver123!')
            driver_1.save()

            driver_2, _ = DriverUser.objects.get_or_create(
                email='driver2@saferoute.com',
                defaults={'first_name': 'Mark', 'last_name': 'Driver', 'phone_number': '+1234567892', 'is_verified': True}
            )
            driver_2.set_password('Driver123!')
            driver_2.save()

            assistant_1, _ = AssistantUser.objects.get_or_create(
                email='assistant1@saferoute.com',
                defaults={'first_name': 'Jane', 'last_name': 'Assistant', 'phone_number': '+1234567893', 'is_verified': True}
            )
            assistant_1.set_password('Assistant123!')
            assistant_1.save()

            assistant_2, _ = AssistantUser.objects.get_or_create(
                email='assistant2@saferoute.com',
                defaults={'first_name': 'Sarah', 'last_name': 'Assistant', 'phone_number': '+1234567894', 'is_verified': True}
            )
            assistant_2.set_password('Assistant123!')
            assistant_2.save()

            # ---------------------------------------------------------
            # 2. Create Guardian Accounts & Locations
            # ---------------------------------------------------------
            guardian_1, _ = GuardianUser.objects.get_or_create(
                email='guardian1@saferoute.com',
                defaults={'first_name': 'Mary', 'last_name': 'Smith', 'phone_number': '+1234567895', 'is_verified': True}
            )
            guardian_1.set_password('Guardian123!')
            guardian_1.save()

            guardian_2, _ = GuardianUser.objects.get_or_create(
                email='guardian2@saferoute.com',
                defaults={'first_name': 'Paul', 'last_name': 'Jones', 'phone_number': '+1234567896', 'is_verified': True}
            )
            guardian_2.set_password('Guardian123!')
            guardian_2.save()

            guard_1_home, _ = StudentSavedLocation.objects.get_or_create(
                guardian=guardian_1, description='Smith Family House',
                defaults={'latitude': 30.012345, 'longitude': 31.012345, 'is_active': True}
            )
            guard_1_grandma, _ = StudentSavedLocation.objects.get_or_create(
                guardian=guardian_1, description='Grandma Residence',
                defaults={'latitude': 30.044000, 'longitude': 31.044000, 'is_active': True}
            )
            guard_2_home, _ = StudentSavedLocation.objects.get_or_create(
                guardian=guardian_2, description='Jones Family Villa',
                defaults={'latitude': 30.055345, 'longitude': 31.055345, 'is_active': True}
            )

            # ---------------------------------------------------------
            # 3. Create Children
            # ---------------------------------------------------------
            child_1, _ = Child.objects.get_or_create(
                guardian=guardian_1, first_name='Jimmy', last_name='Smith',
                defaults={'grade': '3rd Grade', 'pickup_pin': '1111', 'is_active': True}
            )
            child_2, _ = Child.objects.get_or_create(
                guardian=guardian_1, first_name='Sally', last_name='Smith',
                defaults={'grade': '1st Grade', 'pickup_pin': '2222', 'is_active': True}
            )
            child_3, _ = Child.objects.get_or_create(
                guardian=guardian_2, first_name='Tommy', last_name='Jones',
                defaults={'grade': '5th Grade', 'pickup_pin': '3333', 'is_active': True}
            )
            child_4, _ = Child.objects.get_or_create(
                guardian=guardian_2, first_name='Lily', last_name='Jones',
                defaults={'grade': 'Kindergarten', 'pickup_pin': '4444', 'is_active': True}
            )

            # Create a pending Location Change Request for child 1
            change_req, created = LocationChangeRequest.objects.get_or_create(
                guardian=guardian_1,
                target_date=timezone.now().date(),
                status=LocationChangeStatus.PENDING_REVIEW,
                defaults={
                    'change_type': LocationChangeType.DROPOFF,
                    'new_location': guard_1_grandma
                }
            )
            if created:
                change_req.students.add(child_1)

            # ---------------------------------------------------------
            # 4. Create Buses & Routes
            # ---------------------------------------------------------
            bus_am, _ = Bus.objects.get_or_create(
                plate_number='AM-1111',
                defaults={'model': 'Yellow Minibus', 'capacity': 15, 'driver': driver_1, 'status': BusStatusChoices.AVAILABLE}
            )
            bus_pm, _ = Bus.objects.get_or_create(
                plate_number='PM-2222',
                defaults={'model': 'Large Coach', 'capacity': 50, 'driver': driver_2, 'status': BusStatusChoices.AVAILABLE}
            )

            route_am, _ = Route.objects.get_or_create(
                name='Morning Sector A',
                defaults={
                    'description': 'Typical AM pickup', 'school_name': 'SafeRoute Academy',
                    'school_latitude': 30.050000, 'school_longitude': 31.050000, 'bus': bus_am
                }
            )
            route_pm, _ = Route.objects.get_or_create(
                name='Afternoon Sector A',
                defaults={
                    'description': 'Typical PM dropoff', 'school_name': 'SafeRoute Academy',
                    'school_latitude': 30.050000, 'school_longitude': 31.050000, 'bus': bus_pm
                }
            )

            # Morning Stops
            stop_1_am, _ = RouteStop.objects.get_or_create(route=route_am, order=1, defaults={'name': 'Smith Entrance', 'latitude': 30.012500, 'longitude': 31.012500})
            stop_2_am, _ = RouteStop.objects.get_or_create(route=route_am, order=2, defaults={'name': 'Jones Corner', 'latitude': 30.020000, 'longitude': 31.020000})

            # Afternoon Stops (reverse order roughly)
            stop_1_pm, _ = RouteStop.objects.get_or_create(route=route_pm, order=1, defaults={'name': 'Jones Corner', 'latitude': 30.020000, 'longitude': 31.020000})
            stop_2_pm, _ = RouteStop.objects.get_or_create(route=route_pm, order=2, defaults={'name': 'Smith Entrance', 'latitude': 30.012500, 'longitude': 31.012500})

            # Base Assign kids to routes
            RouteChild.objects.get_or_create(route=route_am, child=child_1, defaults={'stop': stop_1_am})
            RouteChild.objects.get_or_create(route=route_am, child=child_2, defaults={'stop': stop_1_am})
            RouteChild.objects.get_or_create(route=route_am, child=child_3, defaults={'stop': stop_2_am})
            RouteChild.objects.get_or_create(route=route_am, child=child_4, defaults={'stop': stop_2_am})

            RouteChild.objects.get_or_create(route=route_pm, child=child_1, defaults={'stop': stop_2_pm})
            RouteChild.objects.get_or_create(route=route_pm, child=child_2, defaults={'stop': stop_2_pm})
            RouteChild.objects.get_or_create(route=route_pm, child=child_3, defaults={'stop': stop_1_pm})
            RouteChild.objects.get_or_create(route=route_pm, child=child_4, defaults={'stop': stop_1_pm})

            # ---------------------------------------------------------
            # 5. Create Trips for Today
            # ---------------------------------------------------------
            today = timezone.now().date()
            
            # AM Trip
            trip_am, _ = Trip.objects.get_or_create(
                route=route_am, scheduled_date=today, trip_type=TripTypeChoices.PICKUP,
                defaults={
                    'status': TripStatusChoices.SCHEDULED, 'driver': driver_1, 'assistant': assistant_1, 'bus': bus_am,
                    'current_latitude': 30.010000, 'current_longitude': 31.010000
                }
            )
            # Add kids to today's AM trip
            for child, stop in [(child_1, stop_1_am), (child_2, stop_1_am), (child_3, stop_2_am), (child_4, stop_2_am)]:
                TripChild.objects.get_or_create(trip=trip_am, child=child, defaults={'stop': stop, 'status': TripChildStatusChoices.WAITING})

            # PM Trip
            trip_pm, _ = Trip.objects.get_or_create(
                route=route_pm, scheduled_date=today, trip_type=TripTypeChoices.DROPOFF,
                defaults={
                    'status': TripStatusChoices.SCHEDULED, 'driver': driver_2, 'assistant': assistant_2, 'bus': bus_pm,
                    'current_latitude': 30.060000, 'current_longitude': 31.060000
                }
            )
            for child, stop in [(child_3, stop_1_pm), (child_4, stop_1_pm), (child_1, stop_2_pm), (child_2, stop_2_pm)]:
                TripChild.objects.get_or_create(trip=trip_pm, child=child, defaults={'stop': stop, 'status': TripChildStatusChoices.WAITING})

            self.stdout.write(self.style.SUCCESS('\nSuccessfully generated a massive amount of dummy data!'))
            
            # Print accounts for the user
            self.stdout.write('\n--- 🔑 Login Accounts 🔑 ---')
            self.stdout.write('Admin:        admin@saferoute.com')
            self.stdout.write('Driver AM:    driver1@saferoute.com    (Assigned to Morning Pickup)')
            self.stdout.write('Driver PM:    driver2@saferoute.com    (Assigned to Afternoon Dropoff)')
            self.stdout.write('Assistant AM: assistant1@saferoute.com')
            self.stdout.write('Assistant PM: assistant2@saferoute.com')
            self.stdout.write('Guardian 1:   guardian1@saferoute.com  (Parent of Jimmy & Sally)')
            self.stdout.write('Guardian 2:   guardian2@saferoute.com  (Parent of Tommy & Lily)')
            self.stdout.write('\nPass:         [Role]123! (e.g. Driver123!)')
