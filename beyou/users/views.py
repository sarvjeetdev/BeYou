from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        # Get the number of login attempts
        login_attempts = cache.get(f'login_attempts_{username}', 0)
        
        # Check if too many attempts
        if login_attempts >= 5:
            messages.error(request, 'Too many login attempts. Please try again later.')
            return render(request, 'users/login.html', {'form': AuthenticationForm()})
            
        # Proceed with normal login logic...
        # If login fails, increment the counter
        cache.set(f'login_attempts_{username}', login_attempts + 1, 300)  # 5 minutes timeout

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out!')
    return redirect('login')

def landing_page(request):
    return render(request, 'users/landing.html')

