import os
import sys
import django
import random

# 1. Configuration du chemin
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 2. Utilisation du nom de projet détecté
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_web.settings')

# 3. Initialisation
try:
    django.setup()
    print("✅ Django initialisé (Projet: parking_web)")
except Exception as e:
    print(f"❌ Erreur : {e}")
    sys.exit(1)

# 4. Imports avec TES noms de classes exacts
from django.utils import timezone
from management.models import Zone, VehicleType, Vehicle, ParkingSlot, ParkingSession

def seed_parking():
    print("🚀 Remplissage du parking en cours...")

    # Création/Récupération d'un type de véhicule par défaut
    v_type, _ = VehicleType.objects.get_or_create(name="Berline")

    vehicles_data = [
        ("ABC-123-A", "Audi A4"), ("DFG-456-B", "Golf 8"),
        ("HJK-789-C", "Mercedes C"), ("LMP-012-D", "BMW Serie 3"),
        ("QRS-345-E", "Renault Clio"), ("TUV-678-F", "Peugeot 208"),
        ("WXY-901-G", "Tesla Model 3"), ("ZAB-234-H", "Dacia Sandero"),
        ("CDE-567-I", "Ford Focus"), ("FGH-890-J", "Hyundai Tucson"),
    ]

    # Récupérer les places libres (ParkingSlot)
    # On filtre par 'available' (vérifie si c'est bien la valeur dans ton models.py)
    available_slots = list(ParkingSlot.objects.filter(status='available'))

    if not available_slots:
        print("❌ Aucune place libre 'available' trouvée.")
        print("💡 Conseil : Vérifie tes objets ParkingSlot dans l'admin Django.")
        return

    random.shuffle(available_slots)
    count = min(len(available_slots), 10)

    for i in range(count):
        plate, brand = vehicles_data[i]
        slot = available_slots[i]

        # Créer le véhicule lié au type
        vehicle, _ = Vehicle.objects.get_or_create(
            plate_number=plate,
            defaults={'vehicle_type': v_type} 
        )

        # Création de la session (entrée il y a 1h à 3h)
        entry_time = timezone.now() - timezone.timedelta(minutes=random.randint(60, 180))
        
        ParkingSession.objects.create(
            vehicle=vehicle,
            slot=slot,
            entry_time=entry_time
        )

        # Mise à jour du statut de la place
        slot.status = 'occupied'
        slot.save()
        print(f"  [+] {plate} ({brand}) -> Place {slot.slot_number}")

    print(f"\n✨ Opération terminée : {count} véhicules ajoutés.")

if __name__ == "__main__":
    seed_parking()