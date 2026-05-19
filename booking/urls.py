from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BarberViewSet, ServiceViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'barbers', BarberViewSet, basename='barber')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('v1/', include(router.urls)), # Усі маршрути будуть починатися з api/v1/...
]