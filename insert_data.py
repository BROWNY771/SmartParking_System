import os
import sys
import django
import random
import string

# 1. Configuration du chemin
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 2. Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_web.settings')

# 3. Initialisation
try:
    django.setup()
    print("✅ Django initialisé (Projet: parking_web)")
except Exception as e:
    print(f"❌ Erreur : {e}")
    sys.exit(1)

from django.utils import timezone
from management.models import VehicleType, Vehicle, ParkingSlot, ParkingSession

def generate_moroccan_plate():
    """Génère une plaque au format : 12345-A-6 (Ex: Rabat=1, Casa=6, Salé=2)"""
    numbers = random.randint(100, 99999)
    # Lettres communes sur les plaques marocaines
    letters = ['A', 'B', 'D', 'H', 'J', 'W', 'P'] 
    letter = random.choice(letters)
    prefecture = random.randint(1, 88) # Codes préfectures (1=Rabat, 6=Casa, etc.)
    return f"{numbers}-{letter}-{prefecture}"

def seed_parking():
    print("🚀 Remplissage du parking avec des immatriculations marocaines...")

    # Récupération ou création des types pour varier
    type_berline, _ = VehicleType.objects.get_or_create(name="Berline", defaults={'extra_rate': 0})
    type_suv, _ = VehicleType.objects.get_or_create(name="SUV/4x4", defaults={'extra_rate': 5})
    
    vehicle_types = [type_berline, type_suv]
    brands = ["Dacia Logan", "Renault Clio", "Golf 7", "Range Rover", "Toyota Hilux", "Peugeot 208", "Fiat 500", "Hyundai Accent"]

    # Récupérer TOUTES les places libres
    available_slots = list(ParkingSlot.objects.filter(status='available'))

    if not available_slots:
        print("❌ Aucune place libre trouvée.")
        return

    # On décide de remplir 70% des places libres pour laisser un peu de vide
    num_to_fill = int(len(available_slots) * 0.7)
    random.shuffle(available_slots)
    
    slots_to_occupy = available_slots[:num_to_fill]

    count = 0
    for slot in slots_to_occupy:
        plate = generate_moroccan_plate()
        v_type = random.choice(vehicle_types)
        
        # 1. Créer ou récupérer le véhicule
        vehicle, _ = Vehicle.objects.get_or_create(
            plate_number=plate,
            defaults={'vehicle_type': v_type}
        )

        # 2. Création de la session (entre 30 min et 5 heures de présence)
        entry_time = timezone.now() - timezone.timedelta(minutes=random.randint(30, 300))
        
        # On vérifie s'il n'y a pas déjà une session active (sécurité)
        if not ParkingSession.objects.filter(slot=slot, exit_time__isnull=True).exists():
            ParkingSession.objects.create(
                vehicle=vehicle,
                slot=slot,
                entry_time=entry_time
            )

            # 3. Mise à jour du statut de la place
            slot.status = 'occupied'
            slot.save()
            
            brand = random.choice(brands)
            print(f"  [+] {plate} ({brand}) -> Zone {slot.zone.name} | Place {slot.slot_number}")
            count += 1

    print(f"\n✨ Opération terminée : {count} véhicules marocains ajoutés au parking.")

if __name__ == "__main__":
    seed_parking()