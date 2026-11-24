from django.urls import path
from .views import *

urlpatterns = [
    path("registration/", registration, name="registration"),
    path("confirm_email/", confirm_email, name="confirm_email"),
    path("login/", login_user, name="login"),
    path("profile/", show_profile, name="profile"),
    path('', show_profile, name='home'),
    path('tasks/create/', create_task, name='task_create'),
    path('tasks/<int:task_id>/', read_task, name='task_detail'),
    path('tasks/<int:task_id>/update/', task_update, name='task_update'),
    path('tasks/<int:task_id>/delete/', task_delete, name='task_delete'),
]
