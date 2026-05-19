from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Service name")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    duration = models.IntegerField(help_text="Duration in minutes", verbose_name="Duration")
    icon_name = models.CharField(max_length=50, verbose_name="SVG Icon Name")
    description = models.TextField(blank=True, null=True, verbose_name="Service description")

    def __str__(self):
        return f"{self.name} (${self.price})"
    
class Barber(models.Model):
    name = models.CharField(max_length=100, verbose_name="Barber name")
    experience = models.CharField(max_length=50, verbose_name="Experience")
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=4.0,
        verbose_name="Rating"
    )
    photo_URL = models.ImageField(upload_to='barbers/', blank=True, null=True, verbose_name="Photo")
    services = models.ManyToManyField(Service, related_name='barbers', verbose_name="Barber services")

    def __str__(self):
        return self.name

class Customer(models.Model):
    fullname = models.CharField(max_length=150, verbose_name="Full name")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Phone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    def __str__(self):
        return self.fullname
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name='appointments', verbose_name="Barber")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments', verbose_name="Customer")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments', verbose_name="Selected service")

    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Time")

    comment = models.TextField(blank=True, null=True, verbose_name="Customer comment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")

    class Meta:
        # Захист від дублювання: один барбер не може бути зайнятий двома людьми на один і той самий час
        unique_together = ('barber', 'date', 'time')
        ordering = ['-date', '-time']

    def __str__(self):
        return f"Запис №{self.id}: {self.customer.fullname} -> {self.barber.name} ({self.date} {self.time})"

