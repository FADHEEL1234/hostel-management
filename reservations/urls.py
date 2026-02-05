from django.urls import path
from . import views

urlpatterns = [
    path("accounts/signup/", views.signup, name="signup"),
    path("", views.home, name="home"),
    path("hostels/<int:hostel_id>/", views.hostel_detail, name="hostel_detail"),
    path("hostels/<int:hostel_id>/book/", views.book_hostel, name="book_hostel"),
    path("bookings/<int:booking_id>/success/", views.booking_success, name="booking_success"),
    path("bookings/<int:booking_id>/payment/", views.booking_payment, name="booking_payment"),
    path("bookings/<int:booking_id>/receipt/", views.booking_receipt, name="booking_receipt"),
    path("bookings/", views.bookings_list, name="bookings_list"),
]
