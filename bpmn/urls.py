from django.urls import path
from . import views

app_name = "bpmn"

urlpatterns = [
    path('', views.home_view, name="home"),
    path('upload-file', views.load_file_view, name="upload-file"),
    path('diagram/', views.diagram_view, name="diagram"),
]


