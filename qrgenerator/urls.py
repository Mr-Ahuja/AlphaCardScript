from django.urls import path
from .views import Home
from .views import upload
from .views import job



urlpatterns = [
    path('', Home),
    path('upload/', upload, name='upload'),
    path('<str:job_id>/', job, name='job')
]