from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:user_id>/', views.view_messages, name='view-messages'),
]