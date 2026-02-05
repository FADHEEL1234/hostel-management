import os
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Hostel, Booking
from .forms import BookingForm, SignupForm, PaymentForm


@login_required
def home(request):
    hostels = Hostel.objects.prefetch_related("amenities").all().order_by("name")
    return render(request, "reservations/home.html", {"hostels": hostels})


@login_required
def hostel_detail(request, hostel_id):
    hostel = get_object_or_404(Hostel, id=hostel_id)
    rooms = hostel.rooms.all().order_by("price_per_night")
    return render(request, "reservations/hostel_detail.html", {"hostel": hostel, "rooms": rooms})


@login_required
def book_hostel(request, hostel_id):
    hostel = get_object_or_404(Hostel, id=hostel_id)
    rooms = hostel.rooms.all().order_by("price_per_night")

    if request.method == "POST":
        form = BookingForm(request.POST, room_queryset=rooms)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.hostel = hostel
            booking.user = request.user
            booking.save()
            return redirect(reverse("booking_success", args=[booking.id]))
    else:
        form = BookingForm(room_queryset=rooms)

    return render(request, "reservations/booking_form.html", {"hostel": hostel, "form": form})


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "reservations/booking_success.html", {"booking": booking})


@login_required
def bookings_list(request):
    bookings = (
        Booking.objects.select_related("hostel", "room")
        .filter(user=request.user)
        .order_by("-created_at")
    )
    return render(request, "reservations/bookings_list.html", {"bookings": bookings})


@login_required
def booking_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            booking.mark_paid()
            return redirect("booking_success", booking_id=booking.id)
    else:
        form = PaymentForm()

    return render(
        request,
        "reservations/booking_payment.html",
        {"booking": booking, "form": form},
    )


@login_required
def booking_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if not booking.is_paid:
        return redirect("booking_payment", booking_id=booking.id)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    def format_tzs(value):
        if value is None:
            return "TZS 0"
        if not isinstance(value, Decimal):
            try:
                value = Decimal(value)
            except Exception:
                return f"TZS {value}"
        return f"TZS {value:,.0f}"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="receipt-{booking.id}.pdf"'

    c = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    c.setFillColor(colors.HexColor("#1b2a3a"))
    c.rect(0, height - 95, width, 95, fill=1, stroke=0)

    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, height - 85, width=70, height=70, preserveAspectRatio=True, mask="auto")

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(130, height - 55, "STUDENT HUB HOSTEL")
    c.setFont("Helvetica", 10)
    c.drawString(130, height - 72, "Booking Receipt")

    c.setFillColor(colors.HexColor("#1b2a3a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 130, "Receipt Details")

    c.setStrokeColor(colors.HexColor("#d3dce6"))
    c.setLineWidth(1)
    c.line(40, height - 138, width - 40, height - 138)

    details = [
        ("Receipt No:", booking.receipt_number),
        ("Date:", booking.paid_at.strftime("%Y-%m-%d %H:%M")),
        ("Guest:", booking.guest_name),
        ("Email:", booking.guest_email),
        ("Hostel:", booking.hostel.name),
        ("Room:", booking.room.name),
        ("Dates:", f"{booking.check_in} to {booking.check_out}"),
        ("Nights:", str(booking.nights)),
    ]

    y = height - 165
    c.setFont("Helvetica", 10.5)
    for label, value in details:
        c.setFillColor(colors.HexColor("#5a6b7b"))
        c.drawString(40, y, label)
        c.setFillColor(colors.HexColor("#1b2a3a"))
        c.drawString(130, y, str(value))
        y -= 18

    c.setFillColor(colors.HexColor("#f4f7fb"))
    c.rect(40, y - 30, width - 80, 40, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1b2a3a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, "Total Paid")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 50, y - 10, format_tzs(booking.amount_paid))

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#8a97a6"))
    c.drawString(40, 60, "Thank you for choosing Student Hub Hostel.")
    c.drawRightString(width - 40, 60, "support@studenthubhostel.com")

    c.showPage()
    c.save()
    return response


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("home")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("/admin/")
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        form.fields["username"].widget.attrs.update({"placeholder": "Email ID or Username"})
        form.fields["password"].widget.attrs.update({"placeholder": "Password"})
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect("/admin/")
            return redirect("home")
    else:
        form = AuthenticationForm(request)
        form.fields["username"].widget.attrs.update({"placeholder": "Email ID or Username"})
        form.fields["password"].widget.attrs.update({"placeholder": "Password"})

    return render(request, "registration/login.html", {"form": form})
