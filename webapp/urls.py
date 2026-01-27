from django.urls import path
from .views import webapp_view

urlpatterns = [
    path("", webapp_view),
    path("dashboard", webapp_view),
]
