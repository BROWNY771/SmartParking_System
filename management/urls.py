from django.contrib import admin
from django.urls import path
from management import views  # <--- AJOUTE CETTE LIGNE

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
    path('check-in/', views.check_in, name='check_in'),
    path('checkout/<int:session_id>/', views.checkout_vehicle, name='checkout_vehicle'),
]