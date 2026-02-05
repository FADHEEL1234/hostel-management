from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Hostel(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="hostels/", blank=True, null=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="hostels")

    def __str__(self):
        return f"{self.name} ({self.city})"


class Room(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    beds = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    is_private = models.BooleanField(default=False)
    image = models.ImageField(upload_to="rooms/", blank=True, null=True)

    def __str__(self):
        return f"{self.hostel.name} - {self.name}"


class Booking(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True,
    )
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    guest_name = models.CharField(max_length=120)
    guest_email = models.EmailField()
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    receipt_number = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return f"{self.guest_name} - {self.hostel.name} ({self.check_in} to {self.check_out})"

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @property
    def total_price(self):
        return self.nights * self.room.price_per_night

    def mark_paid(self):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.amount_paid = self.total_price
        if not self.receipt_number:
            self.receipt_number = f"RCPT-{self.id:06d}"
        self.save(update_fields=["is_paid", "paid_at", "amount_paid", "receipt_number"])
