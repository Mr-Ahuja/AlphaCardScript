from django.urls import path
from .views import *

urlpatterns = [
    path('', Home),
    path('penny/',penny),
    path('penny/<str:job_id>/captcha',captcha),
    path('penny/<str:job_id>/delete',penny_delete),
    path('penny/<str:job_id>/',penny_job),
    path('<str:job_id>/retrigger/', retrigger, name='stop_job'),
    path('<str:job_id>/stop/', stop_job, name='stop_job'),
    path('delete/<str:job_id>/', delete_job, name='delete_job'),
    path('upload/', upload, name='upload'),
    path('<str:job_id>/', job, name='job'),
    path('<str:job_id>/<str:reattempt>/', job, name='job_reattempt'),
    path('token/<int:amount>/', load_token, name='load_token'),

]