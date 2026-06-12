from django.urls import path

from . import views

app_name = "workshop"

urlpatterns = [
    path("", views.facilitator, name="facilitator"),
    path("vote/", views.vote, name="vote"),
    path("vote/thanks/", views.thanks, name="thanks"),
    path("results.json", views.results, name="results"),
    path("qr.png", views.qr_code, name="qr_code"),
]
