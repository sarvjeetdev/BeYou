from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginActivity

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Mark request to avoid duplicate logging
    request._login_attempt_logged = True

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    # Create logout entry
    if user and request:
        LoginActivity.objects.create(
            user=user,
            username=user.username,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            was_successful=True,
            failure_reason="User logged out"
        )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip