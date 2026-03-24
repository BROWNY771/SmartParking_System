import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

def insert_parking_data():
    try:
        # 1. Définition des Zones (Nom, Prix, Durée Max)
        zones_to_create = [
            ('Zone Nord (A)', 15.00, 24),
            ('Zone Ouest (B)', 10.00, 12),
            ('Zone Est (C)', 20.00, 48),
            ('Zone Sud (D)', 12.00, 24),
        ]

        print("--- Insertion des Zones ---")
        zone_mapping = {} # Pour stocker {Lettre: ID_réel_BDD}
        
        for name, price, duration in zones_to_create:
            cursor.execute("""
                INSERT INTO management_zone (name, price_per_hour, max_duration) 
                VALUES (?, ?, ?)
            """, (name, price, duration))
            
            last_id = cursor.lastrowid
            # On extrait la lettre (A, B, C ou D) pour lier les slots plus tard
            letter = name.split('(')[1][0] 
            zone_mapping[letter] = last_id
            print(f"✅ {name} créée avec l'ID: {last_id}")

        # 2. Génération automatique des Slots (10 par zone)
        print("\n--- Insertion des Slots ---")
        all_slots = []
        
        for letter, zone_id in zone_mapping.items():
            for i in range(1, 11): # Crée les places de 1 à 10 pour chaque zone
                slot_number = f"{letter}{i}" # Exemple: A1, A2... B1, B2...
                all_slots.append((slot_number, 'available', zone_id))

        cursor.executemany("""
            INSERT INTO management_parkingslot (slot_number, status, zone_id) 
            VALUES (?, ?, ?)
        """, all_slots)

        conn.commit()
        print(f"🚀 Succès total ! {len(all_slots)} places de parking ont été générées.")

    except Exception as e:
        print(f"❌ Erreur lors de l'insertion : {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    insert_parking_data()