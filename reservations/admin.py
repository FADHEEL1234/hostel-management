from django.contrib import admin
from django.utils.html import format_html
from .models import Amenity, Hostel, Room, Booking


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "image_preview"]
    search_fields = ["name", "city"]
    inlines = [RoomInline]
    readonly_fields = ["image_preview"]
    fieldsets = [
        (None, {"fields": ["name", "city", "address", "description", "amenities"]}),
        ("Images", {"fields": ["image"]}),
        ("Preview", {"fields": ["image_preview"]}),
    ]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:160px;border-radius:10px;" />', obj.image.url)
        return "-"

    image_preview.short_description = "Image"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "hostel", "beds", "price_per_night", "is_private", "image_preview"]
    list_filter = ["is_private", "hostel"]
    readonly_fields = ["image_preview"]
    fields = ["hostel", "name", "beds", "price_per_night", "is_private", "image", "image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:8px;" />', obj.image.url)
        return "-"

    image_preview.short_description = "Image"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["guest_name", "user", "hostel", "room", "check_in", "check_out", "created_at"]
    list_filter = ["hostel", "room", "created_at"]
    search_fields = ["guest_name", "guest_email", "user__username", "user__email"]
