from rest_framework import viewsets, mixins
from .models import Barber, Service, Appointment
from .serializers import BarberSerializer, ServiceSerializer, AppointmentCreateSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, time
from .models import Barber, Appointment
from django.utils import timezone
from .serializers import BarberSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint do przeglądania listy usług barbershopu"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer 

class BarberViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint do przeglądania listy barberów oraz ich indywidualnych usług."""
    queryset = Barber.objects.all()
    serializer_class = BarberSerializer

    @extend_schema(
        summary="Pobierz wolne terminy barbera",
        description="Zwraca tablicę dostępnych slotów godzinowych dla konkretnego barbera w wybranym dniu. Uwzględnia dni wolne oraz już istniejące rezerwacje.",
        parameters=[
            OpenApiParameter(
                name='date', 
                description='Data wizyty w formacie YYYY-MM-DD', 
                required=True, 
                type=str
            )
        ]
    )

    @action(detail=True, methods=['get'])
    def free_slots(self, request, pk=None):
        barber = self.get_object()
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({"error": "Parametr 'date' is requared in format YYYY-MM-DD"}, status=400)
        
        try:
            target_data = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Невірний формат дат. Використовуй YYYY-MM-DD"}, status=400)
        
        if target_data.weekday() == 6:
            working_hours = [f"{hour:02d}:00" for hour in range(9, 18)]
        else:
            working_hours = [f"{hour:02d}:00" for hour in range(9, 20)]
        

        taken_appointments = Appointment.objects.filter(
            barber=barber,
            date=target_data
        ).exclude(status='cancelled')

        taken_hours = [app.time.strftime('%H:%M') for app in taken_appointments]

        free_slots = []
        current_time = timezone.localtime() # Поточний час сервера
        current_date = current_time.date()
        current_hour_str = current_time.strftime('%H:%M') # Наприклад, "17:36"

        for slot in working_hours:
            # 1. Перевіряємо, чи час взагалі не зайнятий іншим клієнтом
            if slot not in taken_hours:
                # 2. Якщо юзер дивиться на СЬОГОДНІ, відсікаємо години, які вже пройшли
                if target_data == current_date and slot <= current_hour_str:
                    continue # Пропускаємо цей слот, бо він у минулому
                
                free_slots.append(slot)

        #free_slots = [slot for slot in working_hours if slot not in taken_hours]

        return Response({
            "date": date_str,
            "free_slots": free_slots
        })

@extend_schema(
    methods=['POST'],
    summary="Utwórz nową rezerwację",
    description="Tworzy nową wizytę u wybranego barbera. Jeśli klient o podanym numerze telefonu nie istnieje, zostanie automatycznie utworzony nowy profil w bazie danych."
)
class AppointmentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Endpoint służący wyłącznie do TWORZENIA nowych rezerwacji (POST /api/v1/appointments/)."""
    
    queryset = Appointment.objects.all()
    serializer_class = AppointmentCreateSerializer
