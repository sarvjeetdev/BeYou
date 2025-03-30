from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q
from .models import Conversation, ConversationParticipant, Message
from users.models import CustomUser
from .forms import MessageForm, CreateGroupForm
from friends.models import Notification
from django.conf import settings
from cryptography.fernet import Fernet

@login_required
def conversation_list(request):
    # Get all conversations where the user is a participant
    participant_conversations = ConversationParticipant.objects.filter(user=request.user).select_related('conversation')
    
    conversations = []
    for participant in participant_conversations:
        conversation = participant.conversation
        
        # Get the last message for this conversation
        last_message = Message.objects.filter(conversation=conversation).order_by('-created_at').first()
        
        # For direct conversations, get the other user
        other_user = None
        if conversation.conversation_type == 'direct':
            other_user = conversation.get_other_participant(request.user)
        
        conversations.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': Message.objects.filter(
                conversation=conversation,
                is_read=False
            ).exclude(sender=request.user).count()
        })
    
    return render(request, 'messaging/conversation_list.html', {
        'conversations': conversations
    })


@login_required
def start_conversation(request, user_id):
    print(f"Start conversation called with user_id: {user_id}")
    other_user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if a conversation already exists between these users
    participant_pairs = ConversationParticipant.objects.filter(user=request.user)
    
    existing_conversation = None
    for participant in participant_pairs:
        if participant.conversation.conversation_type == 'direct':
            # Check if the other user is also in this conversation
            if ConversationParticipant.objects.filter(
                conversation=participant.conversation,
                user=other_user
            ).exists():
                existing_conversation = participant.conversation
                break
    
    if existing_conversation:
        return redirect('view_conversation', conversation_id=existing_conversation.id)
    
    # Create a new conversation
    conversation = Conversation.objects.create(conversation_type='direct')
    
    # Add both users as participants
    ConversationParticipant.objects.create(conversation=conversation, user=request.user)
    ConversationParticipant.objects.create(conversation=conversation, user=other_user)
    
    return redirect('view_conversation', conversation_id=conversation.id)


@login_required
def view_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if the user is a participant
    participant = get_object_or_404(ConversationParticipant, conversation=conversation, user=request.user)
    
    # Get other participants
    participants = conversation.participants.exclude(user=request.user)
    
    # Mark messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    # Get messages
    messages_qs = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    # Decrypt messages and prepare for display
    messages_list = []
    key = settings.ENCRYPTION_KEY.encode()
    f = Fernet(key)
    
    for msg in messages_qs:
        message_data = {
            'id': msg.id,
            'sender': msg.sender,
            'created_at': msg.created_at,
            'is_mine': msg.sender == request.user,
            'is_media': msg.is_media_message,
            'media_type': msg.media_type,
            'media_url': msg.media_file.url if msg.media_file else None,
        }
        
        # Get decrypted content if exists
        if msg.encrypted_content:
            try:
                message_data['content'] = f.decrypt(msg.encrypted_content.encode()).decode()
            except Exception as e:
                message_data['content'] = "[Encrypted message]"
        else:
            message_data['content'] = ""
        
        messages_list.append(message_data)
    
    # Handle message form
    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.cleaned_data.get('content')
            media_file = form.cleaned_data.get('media_file')
            media_type = form.cleaned_data.get('media_type')
            
            # Verify the user is verified for media sharing
            if media_file and not request.user.is_verified:
                django_messages.warning(request, "You need to verify your account to send media.")
                return redirect('verification_request')
            
            # Create message
            message = Message(
                conversation=conversation,
                sender=request.user,
                media_type=media_type if media_file else 'none'
            )
            
            # Add content if provided
            if content:
                message.encrypt_message(content)
            
            # Add media if provided
            if media_file:
                message.media_file = media_file
            
            message.save()
            
            # Create notifications for other participants
            for participant in participants:
                notification_content = "New message from {0}".format(request.user.username)
                if message.is_media_message:
                    notification_content = "{0} sent a {1}".format(
                        request.user.username, 
                        "photo" if message.is_image else "video"
                    )
                
                Notification.objects.create(
                    user=participant.user,
                    notification_type='message',
                    content=notification_content,
                    related_user=request.user
                )
            
            return redirect('view_conversation', conversation_id=conversation.id)
    
    return render(request, 'messaging/view_conversation.html', {
        'conversation': conversation,
        'participants': participants,
        'messages_list': messages_list,
        'form': form,
        'is_group': conversation.is_group,
        'is_admin': participant.is_admin,
        'is_verified': request.user.is_verified
    })


@login_required
def create_group(request):
    # Only verified users can create groups
    if not request.user.is_verified:
        django_messages.error(request, "You need to be verified to create group conversations.")
        return redirect('verification_request')
    
    form = CreateGroupForm(user=request.user)
    
    if request.method == 'POST':
        form = CreateGroupForm(request.POST, user=request.user)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.conversation_type = 'group'
            conversation.save()
            
            # Add creator as admin
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=request.user,
                is_admin=True
            )
            
            # Add other participants
            for user in form.cleaned_data['participants']:
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=user
                )
                
                # Notify participants
                Notification.objects.create(
                    user=user,
                    notification_type='group_invite',
                    content=f"{request.user.username} added you to the group '{conversation.name}'",
                    related_user=request.user
                )
            
            django_messages.success(request, f"Group '{conversation.name}' created successfully.")
            return redirect('view_conversation', conversation_id=conversation.id)
    
    return render(request, 'messaging/create_group.html', {'form': form})


@login_required
def remove_from_group(request, conversation_id, user_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, conversation_type='group')
    
    # Check if the requester is an admin
    requester_participant = get_object_or_404(
        ConversationParticipant, 
        conversation=conversation,
        user=request.user,
        is_admin=True
    )
    
    # Get the participant to remove
    participant = get_object_or_404(
        ConversationParticipant,
        conversation=conversation,
        user_id=user_id
    )
    
    # Don't allow removing yourself
    if participant.user == request.user:
        django_messages.error(request, "You cannot remove yourself from the group. Leave the group instead.")
        return redirect('view_conversation', conversation_id=conversation.id)
    
    # Remove the participant
    user_name = participant.user.username
    participant.delete()
    
    django_messages.success(request, f"{user_name} has been removed from the group.")
    return redirect('view_conversation', conversation_id=conversation.id)


@login_required
def leave_group(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, conversation_type='group')
    
    # Get the participant
    participant = get_object_or_404(
        ConversationParticipant,
        conversation=conversation,
        user=request.user
    )
    
    # Check if this is the last admin
    is_last_admin = participant.is_admin and not ConversationParticipant.objects.filter(
        conversation=conversation,
        is_admin=True
    ).exclude(user=request.user).exists()
    
    if is_last_admin:
        # Find other participants
        other_participants = ConversationParticipant.objects.filter(
            conversation=conversation
        ).exclude(user=request.user)
        
        if other_participants.exists():
            # Make someone else admin
            new_admin = other_participants.first()
            new_admin.is_admin = True
            new_admin.save()
            
            # Notify the new admin
            Notification.objects.create(
                user=new_admin.user,
                notification_type='group_invite',
                content=f"You are now an admin of the group '{conversation.name}'",
                related_user=request.user
            )
    
    # Remove the participant
    participant.delete()
    
    django_messages.success(request, f"You have left the group '{conversation.name}'.")
    return redirect('conversation_list')


@login_required
def delete_group(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, conversation_type='group')
    
    # Check if the requester is an admin
    requester_participant = get_object_or_404(
        ConversationParticipant, 
        conversation=conversation,
        user=request.user,
        is_admin=True
    )
    
    # Get all participants to notify them
    participants = ConversationParticipant.objects.filter(
        conversation=conversation
    ).exclude(user=request.user)
    
    # Notify all participants
    for participant in participants:
        Notification.objects.create(
            user=participant.user,
            notification_type='group_invite',
            content=f"The group '{conversation.name}' has been deleted by {request.user.username}",
            related_user=request.user
        )
    
    # Delete the conversation (this will cascade delete all messages and participants)
    conversation_name = conversation.name
    conversation.delete()
    
    django_messages.success(request, f"Group '{conversation_name}' has been deleted.")
    return redirect('conversation_list')


@login_required
def view_media(request, message_id):
    # Get the message
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is participant in conversation
    participant = get_object_or_404(
        ConversationParticipant,
        conversation=message.conversation,
        user=request.user
    )
    
    # Make sure it's a media message
    if not message.is_media_message:
        django_messages.error(request, "This message does not contain media.")
        return redirect('view_conversation', conversation_id=message.conversation.id)
    
    return render(request, 'messaging/view_media.html', {
        'message': message,
        'conversation': message.conversation
    })