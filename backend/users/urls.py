from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html', redirect_field_name='next',next_page='profile'),name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('verification/pending/', views.verification_pending, name='verification_pending'),
    
    # Admin verification URLs
    path('admin/verifications/', views.admin_verification_list, name='admin_verification_list'),
    path('admin/verification/<int:user_id>/', views.process_verification, name='process_verification'),
    
    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/<int:reset_id>/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # TOTP (Two-Factor Authentication) URLs
    path('profile/totp-setup/', views.totp_setup, name='totp_setup'),
]