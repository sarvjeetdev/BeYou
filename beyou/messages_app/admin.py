from django.contrib import admin
from .models import Message

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__username', 'receiver__username', 'content')

admin.site.register(Message, MessageAdmin)
