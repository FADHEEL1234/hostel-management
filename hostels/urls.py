from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from reservations import views as reservation_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", reservation_views.login_view, name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("reservations.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
