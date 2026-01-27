from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls import handler404
from django.conf.urls.static import static

handler404 = 'webapp.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("app.urls")),
    path("", include("webapp.urls")),
]

# Point to your app's view
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)