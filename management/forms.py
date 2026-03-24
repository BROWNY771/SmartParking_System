from django import forms
from .models import ParkingSlot, VehicleType

class CheckInForm(forms.Form):
    plate_number = forms.CharField(
        label="Numéro de Plaque",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'Ex: 12345-A-1',
            'style': 'text-transform: uppercase;'
        })
    )
    
    vehicle_type = forms.ModelChoiceField(
        queryset=VehicleType.objects.all(),
        label="Type de Véhicule",
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    slot = forms.ModelChoiceField(
        # CORRECTION : On autorise TOUTES les zones (A, B, C, D)
        queryset=ParkingSlot.objects.filter(status='available'),
        label="Place de Parking",
        widget=forms.Select(attrs={'class': 'form-input'})
    )