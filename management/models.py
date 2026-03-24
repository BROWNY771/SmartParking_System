from django.db import models
from django.utils import timezone

class Zone(models.Model):
    name = models.CharField(max_length=50)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    max_duration = models.IntegerField(help_text="In hours")

    def __str__(self):
        return self.name

class ParkingSlot(models.Model):
    STATUS_CHOICES = [('available', 'Available'), ('occupied', 'Occupied')]
    slot_number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)

    def __str__(self):
        return f"Slot {self.slot_number} ({self.zone.name})"
    def get_active_session(self):
        return self.parkingsession_set.filter(exit_time__isnull=True).last()

    @property
    def current_vehicle_plate(self):
        session = self.get_active_session()
        return session.vehicle.plate_number if session else ""

    @property
    def current_entry_time(self):
        session = self.get_active_session()
        return session.entry_time.strftime("%H:%M") if session else ""
class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=30)

    def __str__(self):
        return self.plate_number

class ParkingSession(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_price(self):
        if self.exit_time:
            duration = (self.exit_time - self.entry_time).total_seconds() / 3600
            self.total_price = float(duration) * float(self.slot.zone.price_per_hour)
            self.save()