from django.contrib import admin
from .models import Zone, ParkingSlot, Vehicle, ParkingSession

# Cela permet d'afficher tes tables dans l'interface admin
admin.site.register(Zone)
admin.site.register(ParkingSlot)
admin.site.register(Vehicle)
admin.site.register(ParkingSession)