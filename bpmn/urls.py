from django.urls import path
from . import views

app_name = "bpmn"

urlpatterns = [
    path('', views.home_view),
]