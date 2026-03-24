from django.db import models
from django.utils import timezone
import math

class Zone(models.Model):
    name = models.CharField(max_length=50)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2, help_text="Prix de base de la zone")
    max_duration = models.IntegerField(help_text="En heures")

    def __str__(self):
        return f"{self.name} ({self.price_per_hour} DH/h)"

class VehicleType(models.Model):
    name = models.CharField(max_length=50)  # Ex: "Voiture", "Moto", "Poids lourd"
    extra_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Supplément pour ce type")

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type.name})"

class ParkingSlot(models.Model):
    STATUS_CHOICES = [('available', 'Available'), ('occupied', 'Occupied')]
    slot_number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)

    def __str__(self):
        return f"Slot {self.slot_number} ({self.zone.name})"

    def get_active_session(self):
        return self.parkingsession_set.filter(exit_time__isnull=True).last()

class ParkingSession(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_price(self):
        if self.exit_time:
            # Calcul de la durée en heures (arrondi au supérieur pour chaque heure entamée)
            duration = (self.exit_time - self.entry_time).total_seconds() / 3600
            hours_to_bill = math.ceil(duration) if duration > 0 else 1
            
            # Tarif cumulé = Tarif de la Zone + Supplément du type de véhicule
            hourly_rate = float(self.slot.zone.price_per_hour) + float(self.vehicle.vehicle_type.extra_rate)
            
            self.total_price = hours_to_bill * hourly_rate
            self.save()