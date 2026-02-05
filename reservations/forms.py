from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Booking, Room


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["guest_name", "guest_email", "check_in", "check_out", "guests", "room"]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        room_queryset = kwargs.pop("room_queryset", Room.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = room_queryset

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        if check_in and check_out and check_out <= check_in:
            raise ValidationError("Check-out must be after check-in.")
        return cleaned


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Username"})
        self.fields["email"].widget.attrs.update({"placeholder": "Email ID"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm Password"})


class PaymentForm(forms.Form):
    METHOD_CHOICES = [
        ("card", "Card"),
        ("cash", "Cash"),
        ("transfer", "Bank transfer"),
    ]
    method = forms.ChoiceField(choices=METHOD_CHOICES)
    confirm = forms.BooleanField(label="I confirm the payment amount.")
