from django.urls import path
from . import views

urlpatterns = [
    path('', views.friends_list, name='friends-list'),
    path('send/<int:user_id>/', views.send_friend_request, name='send-friend-request'),
    path('accept/<int:request_id>/', views.accept_friend_request, name='accept-friend-request'),
    path('reject/<int:request_id>/', views.reject_friend_request, name='reject-friend-request'),
    path('search/', views.search_users, name='search-users'),
]