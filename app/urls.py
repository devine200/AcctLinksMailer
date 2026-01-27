from django.urls import path
from .views import LoginView, BatchEmailView, SingleEmailView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
    path("email/batch", BatchEmailView.as_view()),
    path("email/single", SingleEmailView.as_view())
]
