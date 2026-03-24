from django import forms
from .models import ParkingSession, ParkingSlot

# Change 'forms.Model' to 'forms.Form'
class CheckInForm(forms.Form):  
    plate_number = forms.CharField(
        max_length=20, 
        widget=forms.TextInput(attrs={'placeholder': 'ABC-1234', 'class': 'form-input'})
    )
    vehicle_type = forms.CharField(
        max_length=30, 
        widget=forms.TextInput(attrs={'placeholder': 'e.g. SUV, Sedan', 'class': 'form-input'})
    )
    
    slot = forms.ModelChoiceField(
        queryset=ParkingSlot.objects.filter(status='available'),
        empty_label="Select an available slot",
        widget=forms.Select(attrs={'class': 'form-input'})
    )