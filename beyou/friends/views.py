from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import FriendRequest

@login_required
def friends_list(request):
    # Get all accepted friend requests
    friends1 = FriendRequest.objects.filter(from_user=request.user, status='accepted')
    friends2 = FriendRequest.objects.filter(to_user=request.user, status='accepted')
    
    # Extract the friend users (not the current user)
    friend_users = []
    for fr in friends1:
        friend_users.append(fr.to_user)
    for fr in friends2:
        friend_users.append(fr.from_user)
    
    # Get pending requests
    pending_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    
    context = {
        'friends': friend_users,
        'pending_requests': pending_requests
    }
    return render(request, 'friends/friends_list.html', context)

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    
    # Check if a request already exists
    if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
        messages.warning(request, 'A friend request was already sent to this user.')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, 'Friend request sent successfully!')
    
    return redirect('search-users')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    messages.success(request, f'You are now friends with {friend_request.from_user.username}')
    return redirect('friends-list')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'rejected'
    friend_request.save()
    messages.info(request, f'Friend request from {friend_request.from_user.username} rejected')
    return redirect('friends-list')

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        # Search for users by username
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    else:
        users = []
    
    return render(request, 'friends/search_users.html', {'users': users, 'query': query})
