import os
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
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

    # Layout inspired by the provided receipt template.
    page_margin = 36
    receipt_width = 300
    receipt_height = height - 2 * page_margin
    receipt_x = page_margin
    receipt_y = page_margin
    aside_x = receipt_x + receipt_width + 28

    # Receipt card
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#d5dbe3"))
    c.setLineWidth(1)
    c.roundRect(receipt_x, receipt_y, receipt_width, receipt_height, 6, fill=1, stroke=1)

    # Logo + header
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            receipt_x + 16,
            height - 110,
            width=58,
            height=58,
            preserveAspectRatio=True,
            mask="auto",
        )
    c.setFillColor(colors.HexColor("#2d3748"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(receipt_x + 80, height - 70, "STUDENT HUB HOSTEL")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(receipt_x + 80, height - 84, "PAYMENT RECEIPT")

    # Key details block
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(receipt_x + 16, height - 135, f"Receipt #: {booking.receipt_number}")
    c.drawString(receipt_x + 16, height - 150, f"Date: {booking.paid_at.strftime('%Y-%m-%d %H:%M')}")

    # Table header
    table_top = height - 185
    c.setFillColor(colors.HexColor("#edf2f7"))
    c.rect(receipt_x + 12, table_top - 20, receipt_width - 24, 20, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#2d3748"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(receipt_x + 18, table_top - 14, "Description")
    c.drawRightString(receipt_x + receipt_width - 18, table_top - 14, "Amount")

    # Table rows
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#2d3748"))
    row_y = table_top - 38
    line_gap = 16
    c.drawString(receipt_x + 18, row_y, f"Hostel: {booking.hostel.name}")
    c.drawRightString(receipt_x + receipt_width - 18, row_y, format_tzs(booking.amount_paid))
    row_y -= line_gap
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(receipt_x + 18, row_y, f"Room: {booking.room.name}")
    row_y -= line_gap
    c.drawString(receipt_x + 18, row_y, f"Dates: {booking.check_in} to {booking.check_out}")
    row_y -= line_gap
    c.drawString(receipt_x + 18, row_y, f"Nights: {booking.nights}")
    row_y -= line_gap
    c.drawString(receipt_x + 18, row_y, f"Guest: {booking.guest_name}")
    row_y -= line_gap
    c.drawString(receipt_x + 18, row_y, f"Email: {booking.guest_email}")

    # Total section
    total_y = receipt_y + 70
    c.setFillColor(colors.HexColor("#f7fafc"))
    c.rect(receipt_x + 12, total_y, receipt_width - 24, 32, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#2d3748"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(receipt_x + 18, total_y + 10, "TOTAL PAID")
    c.drawRightString(receipt_x + receipt_width - 18, total_y + 10, format_tzs(booking.amount_paid))

    # Footer note
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(receipt_x + 16, receipt_y + 30, "Payment confirmed. Thank you for your booking.")

    # Right-side panel (title + tagline)
    c.setFillColor(colors.HexColor("#2d3748"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(aside_x, height - 120, "Payment Receipt")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#4a5568"))
    c.drawString(aside_x, height - 150, "Keep this receipt for your records.")
    c.drawString(aside_x, height - 165, "We appreciate your stay.")

    c.showPage()
    c.save()
    return response


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Registration successful. Welcome!")
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
            messages.success(request, f"Welcome, {user.username}!")
            if user.is_staff or user.is_superuser:
                return redirect("/admin/")
            return redirect("home")
    else:
        form = AuthenticationForm(request)
        form.fields["username"].widget.attrs.update({"placeholder": "Email ID or Username"})
        form.fields["password"].widget.attrs.update({"placeholder": "Password"})

    return render(request, "registration/login.html", {"form": form})
