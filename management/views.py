from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
import qrcode
from django.utils import timezone
from django.db.models import Sum, Count
from django.db import transaction
import io
import math
import json
from decimal import Decimal

# Imports ReportLab pour le PDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from .models import ParkingSlot, ParkingSession, Vehicle, Zone
from .forms import CheckInForm
def dashboard(request):
    total_slots = ParkingSlot.objects.count()
    available_slots = ParkingSlot.objects.filter(status='available').count()
    occupied_slots = ParkingSlot.objects.filter(status='occupied').count()
    all_slots = ParkingSlot.objects.all().order_by('slot_number')
    recent_sessions = ParkingSession.objects.filter(exit_time__isnull=True).order_by('-entry_time')
    
    # Configuration des zones pour le graphique
    zones_config = [
        {'label': 'Zone Nord (A)', 'key': '(A)'},
        {'label': 'Zone Ouest (B)', 'key': '(B)'},
        {'label': 'Zone Est (C)', 'key': '(C)'},
        {'label': 'Zone Sud (D)', 'key': '(D)'} 
    ]
    
    labels = []
    data_chart = [] 

    for item in zones_config:
        labels.append(item['label'])
        # Compte les places occupées par zone
        count = ParkingSlot.objects.filter(
            zone__name__icontains=item['key'], 
            status='occupied'
        ).count()
        data_chart.append(count)

    context = {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'all_slots': all_slots,
        'recent_sessions': recent_sessions,
        'today': timezone.now(),
        'labels': json.dumps(labels),
        'revenues': json.dumps(data_chart), # Utilisé pour le Bar Chart
    }
    return render(request, 'management/dashboard.html', context)
def history(request):
    """Affiche l'historique de toutes les sessions."""
    all_sessions = ParkingSession.objects.all().order_by('-entry_time')
    return render(request, 'management/history.html', {'sessions': all_sessions})

def check_in(request):
    """Enregistre l'entrée d'un véhicule."""
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                plate = form.cleaned_data['plate_number'].upper()
                v_type = form.cleaned_data['vehicle_type']
                slot = form.cleaned_data['slot']

                # Gestion du véhicule (création ou mise à jour)
                vehicle, created = Vehicle.objects.get_or_create(
                    plate_number=plate,
                    defaults={'vehicle_type': v_type}
                )
                
                if not created and vehicle.vehicle_type != v_type:
                    vehicle.vehicle_type = v_type
                    vehicle.save()

                # Création session et occupation de la place
                ParkingSession.objects.create(vehicle=vehicle, slot=slot)
                slot.status = 'occupied'
                slot.save()

                messages.success(request, f"Véhicule {plate} enregistré à la place {slot.slot_number}")
                return redirect('dashboard')
    else:
        form = CheckInForm()
    return render(request, 'management/check_in.html', {'form': form})

def checkout_vehicle(request, session_id):
    """
    1. Calcule le montant final.
    2. Demande confirmation de paiement.
    3. Libère la place et génère le reçu PDF.
    """
    session = get_object_or_404(ParkingSession, id=session_id)
    
    if session.exit_time:
        messages.warning(request, "Ce reçu a déjà été généré.")
        return redirect('dashboard')

    # --- LOGIQUE MÉTIER : CALCUL ---
    now = timezone.now()
    duration = now - session.entry_time
    duration_in_hours = duration.total_seconds() / 3600
    
    # Règle : Min 1h, arrondi au supérieur (ex: 1h05 -> 2h)
    hours_to_bill = math.ceil(max(duration_in_hours, 1.0))
    
    # Tarification basée sur la Zone + Type de véhicule
    base_rate = float(session.slot.zone.price_per_hour)
    extra_rate = float(session.vehicle.vehicle_type.extra_rate)
    total_price = round((base_rate + extra_rate) * hours_to_bill, 2)

    if request.method == 'POST':
        with transaction.atomic():
            # Mise à jour de la session (clôture)
            session.exit_time = now
            session.total_price = total_price
            session.save()
            
            # Libération immédiate de la place
            session.slot.status = 'available'
            session.slot.save()
            
            messages.success(request, f"Paiement de {total_price} DH validé. Reçu généré.")
            return generate_receipt_pdf(session) # Appel de la fonction PDF

    return render(request, 'management/checkout_confirm.html', {
        'session': session,
        'duration_hours': hours_to_bill,
        'total_price': total_price
    })

def generate_receipt_pdf(session):
    """Génère un reçu de paiement avec QR Code vers le site web."""
    buffer = io.BytesIO()
    # Format Ticket Thermique (80mm x 150mm)
    p = canvas.Canvas(buffer, pagesize=(80*mm, 150*mm))
    
    # --- EN-TÊTE ---
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(40*mm, 140*mm, "SMART PARKING")
    p.setFont("Helvetica", 8)
    p.drawCentredString(40*mm, 135*mm, "REÇU DE PAIEMENT")
    p.drawCentredString(40*mm, 131*mm, session.exit_time.strftime("%d/%m/%Y %H:%M"))
    p.line(5*mm, 128*mm, 75*mm, 128*mm)
    
    # --- DÉTAILS DE LA TRANSACTION ---
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10*mm, 120*mm, f"VÉHICULE : {session.vehicle.plate_number}")
    
    p.setFont("Helvetica", 9)
    p.drawString(10*mm, 112*mm, f"Place : {session.slot.slot_number} ({session.slot.zone.name})")
    p.drawString(10*mm, 106*mm, f"Arrivée : {session.entry_time.strftime('%H:%M')}")
    p.drawString(10*mm, 100*mm, f"Départ : {session.exit_time.strftime('%H:%M')}")
    
    p.line(10*mm, 95*mm, 70*mm, 95*mm)
    
    # --- MONTANT FINAL ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(10*mm, 85*mm, "TOTAL PAYÉ")
    p.drawRightString(70*mm, 85*mm, f"{session.total_price} DH")
    
    # --- QR CODE (LIEN VERS LE SITE) ---
    site_url = "http://smartparking.ma" # Ton lien
    qr = qrcode.make(site_url)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    from reportlab.lib.utils import ImageReader
    p.drawImage(ImageReader(qr_buffer), 25*mm, 35*mm, width=30*mm, height=30*mm)
    
    # --- PIED DE PAGE ---
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(40*mm, 30*mm, "www.smartparking-souhail.ma")
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(40*mm, 15*mm, "Merci de votre confiance !")


    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Recu_{session.vehicle.plate_number}.pdf"'
    return response