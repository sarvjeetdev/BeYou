from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Message
from .forms import MessageForm

@login_required
def inbox(request):
    # Get all unique users that the current user has exchanged messages with
    message_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | 
        Q(received_messages__sender=request.user)
    ).distinct()
    
    context = {
        'message_users': message_users
    }
    return render(request, 'messages_app/inbox.html', context)

@login_required
def view_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Get all messages between these two users
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # Mark all received messages as read
    unread_messages = Message.objects.filter(sender=other_user, receiver=request.user, is_read=False)
    for msg in unread_messages:
        msg.is_read = True
        msg.save()
    
    # Handle new message form
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = Message(sender=request.user, receiver=other_user)
            # Encrypt the message content before saving
            message.encrypt_content(form.cleaned_data['content'])
            message.save()
            return redirect('view-messages', user_id=user_id)
    else:
        form = MessageForm()
    
    # Decrypt messages for display
    decrypted_messages = []
    for msg in messages:
        try:
            decrypted_content = msg.decrypted_content
            decrypted_messages.append({
                'id': msg.id,
                'sender': msg.sender,
                'receiver': msg.receiver,
                'content': decrypted_content,
                'timestamp': msg.timestamp,
                'is_read': msg.is_read
            })
        except Exception as e:
            # Handle decryption errors (e.g., if key changes)
            decrypted_messages.append({
                'id': msg.id,
                'sender': msg.sender,
                'receiver': msg.receiver,
                'content': "[Encrypted message - unable to decrypt]",
                'timestamp': msg.timestamp,
                'is_read': msg.is_read
            })
    
    context = {
        'messages': decrypted_messages,
        'other_user': other_user,
        'form': form
    }
    return render(request, 'messages_app/view_messages.html', context)