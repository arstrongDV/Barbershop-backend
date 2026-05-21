from rest_framework import viewsets, mixins
from .models import Barber, Service, Appointment
from .serializers import BarberSerializer, ServiceSerializer, AppointmentCreateSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, time, timedelta
from .models import Barber, Appointment
from django.utils import timezone
from .serializers import BarberSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Sum
import requests
from rest_framework.views import APIView
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination

class BarbersCardPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 50

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint do przeglądania listy usług barbershopu"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer 

class BarberViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint do przeglądania listy barberów oraz ich indywidualnych usług."""
    queryset = Barber.objects.all().order_by('id')
    pagination_class = BarbersCardPagination
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
        print("DEBUG SERVICE IDS:", request.query_params.getlist('service_ids'))
        barber = self.get_object()
        date_str = request.query_params.get('date')
        service_ids = request.query_params.getlist('service_ids')
        

        if not date_str:
            return Response({"error": "Parametr 'date' is requared in format YYYY-MM-DD"}, status=400)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Parametr 'date' is requared in format YYYY-MM-DD"}, status=400)
        
        total_duration = 0
        total_price = 0

        if service_ids:
            clean_service_ids = [int(x) for x in service_ids if str(x).isdigit()]

        if service_ids:
            duration_aggregation = Service.objects.filter(id__in=clean_service_ids).aggregate(total=Sum('duration'))
            price_aggregation = Service.objects.filter(id__in=clean_service_ids).aggregate(total=Sum('price'))
            total_duration = duration_aggregation['total'] or 0
            total_price = price_aggregation['total'] or 0

        if total_duration == 0:
            total_duration = 30

        start_hour = 9
        end_hour = 18 if target_date.weekday() == 6 else 20

        working_slots = []
        current_slot_time = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour))
        end_working_time = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour)) 

        while current_slot_time < end_working_time:
            working_slots.append(current_slot_time.time())
            current_slot_time += timedelta(minutes=30)

        appointments = Appointment.objects.filter(
            barber=barber,
            date=target_date
        ).exclude(status='cancelled').prefetch_related('services')

        taken_intervals = set()
        for app in appointments:
            app_duration = app.services.aggregate(total=Sum('duration'))['total'] or 30
            
            app_start = datetime.combine(target_date, app.time)
            app_end = app_start + timedelta(minutes=app_duration)
            
            # Дробимо цей запис на 30-хвилинні блоки, щоб помітити їх як "зайнято"
            temp = app_start
            while temp < app_end:
                taken_intervals.add(temp.time())
                temp += timedelta(minutes=30)

        free_slots = []
        now_local = timezone.localtime()
        current_date = now_local.date()
        current_time_str = now_local.strftime('%H:%M')

        for slot in working_slots:
            slot_str = slot.strftime('%H:%M')
            
            if target_date == current_date and slot_str <= current_time_str:
                continue
            
            needed_blocks_count = (total_duration + 29) // 30

            is_valid_sequence = True
            slot_datetime = datetime.combine(target_date, slot)

            for i in range(needed_blocks_count):
                check_time = (slot_datetime + timedelta(minutes=i * 30)).time()
                
                if check_time in taken_intervals or check_time >= end_working_time.time():
                    is_valid_sequence = False
                    break
            
            if is_valid_sequence:
                free_slots.append(slot_str)

        return Response({
            "date": date_str,
            "total_duration_minutes": total_duration,
            "total_price": total_price,
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

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    """Endpoint to handle Telegram interactive button clicks"""
    
    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Check if the incoming request is a button click (callback_query)
        if "callback_query" in data:
            callback_query = data["callback_query"]
            callback_data = callback_query["data"]
            message = callback_query["message"]
            chat_id = message["chat"]["id"]
            message_id = message["message_id"]
            
            # Parse the action and appointment ID (e.g., "approve_14")
            try:
                action, appointment_id = callback_data.split("_")
                appointment = Appointment.objects.get(id=int(appointment_id))
                
                # 🌟 Update DB status based on action
                if action == "approve":
                    appointment.status = "confirmed"
                    status_text = "Approved"
                elif action == "cancel":
                    appointment.status = "cancelled"
                    status_text = "Cancelled"
                
                appointment.save()
                
                original_text = message["text"]
                updated_text = f"{original_text}\n\nProcessed: {status_text}"
                
                token = settings.TELEGRAM_BOT_TOKEN
                edit_url = f"https://api.telegram.org/bot{token}/editMessageText"
                
                requests.post(edit_url, json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": updated_text,
                    # Sending empty reply_markup removes the buttons entirely
                    "reply_markup": {"inline_keyboard": []} 
                })
                
                # Answer callback query to stop loading animation on the button
                requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={
                    "callback_query_id": callback_query["id"],
                    "text": f"Appointment status updated to {appointment.status}!"
                })
                
            except (Appointment.DoesNotExist, ValueError) as e:
                print(f"Error processing callback: {e}")
                
        return Response({"status": "ok"})
