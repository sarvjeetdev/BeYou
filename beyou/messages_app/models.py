from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.utils import timezone
from django.conf import settings

# Generate a key and store it in settings.py
# In a real application, you would store this securely in environment variables
if not hasattr(settings, 'ENCRYPTION_KEY'):
    # This is for development only
    # In production, set this in your environment or settings file
    settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()  # This will store encrypted content
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'From {self.sender.username} to {self.receiver.username}'
    
    @property
    def decrypted_content(self):
        """Decrypt and return the message content"""
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        return f.decrypt(self.content.encode()).decode()
    
    def encrypt_content(self, content):
        """Encrypt the provided content and set it to the content field"""
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        self.content = f.encrypt(content.encode()).decode()
    
    def formatted_timestamp(self):
        """Return a nicely formatted timestamp for display"""
        now = timezone.now()
        # If message is from today, show time only
        if self.timestamp.date() == now.date():
            return self.timestamp.strftime('%I:%M %p')  # e.g. "3:45 PM"
        # If message is from this year, show month, day and time
        elif self.timestamp.year == now.year:
            return self.timestamp.strftime('%b %d, %I:%M %p')  # e.g. "Mar 15, 3:45 PM"
        # Otherwise show full date and time
        else:
            return self.timestamp.strftime('%b %d %Y, %I:%M %p')  # e.g. "Mar 15 2023, 3:45 PM"