from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "bpmn"

urlpatterns = [
    path('', views.home_view, name="home"),
    path('upload-file/', views.load_file_view, name="upload-file"),
    path('diagram/', views.diagram_view, name="diagram"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
