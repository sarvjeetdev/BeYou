from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import pyotp
from django.conf import settings
from django.utils import timezone

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)  # TOTP secret for 2FA

    id_document = models.ImageField(upload_to='verification_docs/', null=True, blank=True)
    verification_reason = models.TextField(max_length=500, blank=True, null=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending',
        blank=True, null=True
    )
    verification_submitted_at = models.DateTimeField(null=True, blank=True)
    verification_processed_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)  # Admin notes


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset'),
        ('high_risk', 'High Risk Action'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=128)  # store hashed OTP for security
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.user.username} - {self.purpose}"


class UserKey(models.Model):
    KEY_TYPE_CHOICES = [
        ('signing', 'Signing'),
        ('encryption', 'Encryption'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='keys')
    public_key = models.TextField()
    key_type = models.CharField(max_length=20, choices=KEY_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.key_type.capitalize()} Key for {self.user.username}"


class UserFollow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    followee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followee')

    def __str__(self):
        return f"{self.follower.username} follows {self.followee.username}"


class UserBlock(models.Model):
    blocker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocking')
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_by')
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked_user')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked_user.username}"
    
class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)  # TOTP secret for reset
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Password reset for {self.user.username}"
    
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()