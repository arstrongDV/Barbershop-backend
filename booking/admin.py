from django.contrib import admin
from .models import Service, Barber, Customer, Appointment

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'experience', 'rating', 'get_services')

    def get_services(self, obj):
        # Беремо всі послуги барбера, дістаємо їхні імена і з'єднуємо через кому
        return ", ".join([service.name for service in obj.services.all()])
    
    get_services.short_description = 'Barber services'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'duration')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'fullname', 'phone', 'email')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'barber', 'service', 'date', 'time', 'status')
    list_filter = ('status', 'date', 'barber')