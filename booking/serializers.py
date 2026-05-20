from rest_framework import serializers
from django.utils import timezone
from django.core.validators import RegexValidator
from .models import Barber, Service, Appointment, Customer
from .utils import send_telegram_notification

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Numer telefonu musi być wpisany w formacie: '+999999999'. Od 9 do 15 cyfr."
)

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price', 'duration', 'icon_name', 'description']
        
class BarberSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Barber
        fields = ['id', 'name', 'experience', 'rating', 'photo_URL', 'services']

class AppointmentCreateSerializer(serializers.ModelSerializer):
    customer_fullname = serializers.CharField(write_only=True)
    customer_phone = serializers.CharField(write_only=True, validators=[phone_regex])
    customer_email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'barber', 'services', 'date', 'time', 'comment',
            'customer_fullname', 'customer_phone', 'customer_email'
        ]

    def validate_customer_fullname(self, value):
        clean_name = value.strip()
        
        if len(clean_name) < 2:
            raise serializers.ValidationError("Imię i nazwisko muszą mieć co najmniej 2 znaki!")
        
        if clean_name.isdigit():
            raise serializers.ValidationError("Imię i nazwisko nie mogą składać się tylko z cyfr!")
            
        return clean_name

    def validate_date(self, value):
        today = timezone.localdate()
        
        if value < today:
            raise serializers.ValidationError("Nie można zarezerwować wizyty w przeszłości!")

        return value
    
    def validate(self, attrs):
        barber = attrs.get('barber')
        date = attrs.get('date')
        time = attrs.get('time')

        exists = Appointment.objects.filter(
            barber=barber,
            date=date,
            time=time,
        ).exclude(status='cancelled').exists()

        if exists:
            raise serializers.ValidationError({
                "error": "Ten termin jest już zarezerwowany u wybranego barbera!"
            })
        return attrs

    def create(self, validated_data):
        fullname = validated_data.pop('customer_fullname')
        phone = validated_data.pop('customer_phone')
        email = validated_data.pop('customer_email')

        services_data = validated_data.pop('services', [])

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={'fullname': fullname, 'email': email}
        )

        appointment = Appointment.objects.create(customer=customer, **validated_data)

        appointment.services.set(services_data)

        fresh_appointment = Appointment.objects.prefetch_related('services').get(id=appointment.id)
        
        send_telegram_notification(fresh_appointment)

        return appointment