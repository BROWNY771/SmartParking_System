from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
import io

# Imports ReportLab pour le PDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# IMPORTATION DE TOUS TES MODÈLES ET FORMULAIRES
# Assure-toi que ces noms correspondent exactement à ton fichier models.py et forms.py
from .models import ParkingSlot, ParkingSession, Vehicle 
from .forms import CheckInForm 

def dashboard(request):
    # On récupère les compteurs pour les stats
    total_slots = ParkingSlot.objects.count()
    available_slots = ParkingSlot.objects.filter(status='available').count()
    occupied_slots = ParkingSlot.objects.filter(status='occupied').count()
    
    # Récupérer TOUS les slots pour le plan de masse
    all_slots = ParkingSlot.objects.all().order_by('slot_number')
    
    # Sessions en cours (véhicules garés) pour le tableau
    recent_sessions = ParkingSession.objects.filter(exit_time__isnull=True).order_by('-entry_time')

    context = {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'all_slots': all_slots,
        'recent_sessions': recent_sessions,
        'today': timezone.now(),
    }
    return render(request, 'management/dashboard.html', context)

def history(request):
    all_sessions = ParkingSession.objects.all().order_by('-entry_time')
    return render(request, 'management/history.html', {'sessions': all_sessions})

def check_in(request):
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            # 1. Récupérer ou créer le véhicule
            plate = form.cleaned_data['plate_number']
            v_type = form.cleaned_data['vehicle_type']
            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=plate, 
                defaults={'vehicle_type': v_type}
            )

            # 2. Créer la Session
            slot = form.cleaned_data['slot']
            ParkingSession.objects.create(vehicle=vehicle, slot=slot)

            # 3. Mettre à jour le statut du Slot
            slot.status = 'occupied'
            slot.save()

            messages.success(request, f"Véhicule {plate} enregistré à la place {slot.slot_number}")
            return redirect('dashboard')
    else:
        form = CheckInForm()
    
    return render(request, 'management/check_in.html', {'form': form})

def checkout_vehicle(request, session_id):
    session = get_object_or_404(ParkingSession, id=session_id)
    
    # Marquer la sortie
    session.exit_time = timezone.now()
    
    # --- CALCUL DU PRIX (Exemple : 5 DH / heure) ---
    duration = session.exit_time - session.entry_time
    duration_in_hours = max(1, duration.total_seconds() / 3600)
    prix_total = round(duration_in_hours * 5, 2)
    session.total_price = prix_total # Assure-toi d'avoir ce champ dans ton modèle
    
    session.save()
    
    # Libérer la place
    session.slot.status = 'available'
    session.slot.save()

    # --- GÉNÉRATION DU TICKET PDF ---
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(80*mm, 120*mm))
    
    # En-tête
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(40*mm, 110*mm, "SMART PARKING")
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(40*mm, 105*mm, "Ticket de Sortie")
    p.line(5*mm, 102*mm, 75*mm, 102*mm)

    # Infos véhicule
    p.setFont("Helvetica", 9)
    p.drawString(10*mm, 90*mm, f"Plaque: {session.vehicle.plate_number}")
    p.drawString(10*mm, 82*mm, f"Place: {session.slot.slot_number}")
    
    # Horaires
    p.setFont("Helvetica", 8)
    p.drawString(10*mm, 72*mm, f"Entrée : {session.entry_time.strftime('%d/%m %H:%M')}")
    p.drawString(10*mm, 65*mm, f"Sortie : {session.exit_time.strftime('%d/%m %H:%M')}")
    
    # Prix
    p.line(5*mm, 58*mm, 75*mm, 58*mm)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(10*mm, 50*mm, f"TOTAL : {prix_total} DH")
    
    # Pied de page
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(40*mm, 35*mm, "Merci de votre visite !")

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')