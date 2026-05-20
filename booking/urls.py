from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BarberViewSet, ServiceViewSet, AppointmentViewSet
from booking.views import TelegramWebhookView

router = DefaultRouter()
router.register(r'barbers', BarberViewSet, basename='barber')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/telegram/webhook/', TelegramWebhookView.as_view(), name='telegram_webhook'),
]