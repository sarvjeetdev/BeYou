# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import HttpResponse
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, VerificationForm, PasswordResetRequestForm, PasswordResetVerifyForm, SetNewPasswordForm
from .models import CustomUser, PasswordResetRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
import pyotp
import qrcode
import base64
from io import BytesIO

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}! You are now logged in.')
            return redirect('profile')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user)

    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'users/profile.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'You have successfully logged in!')
            return redirect('profile')  # This should redirect to your profile page
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def verification_request(request):
    """View for users to submit verification requests"""
    user = request.user
    
    # Check if already verified
    if user.is_verified:
        messages.info(request, 'Your account is already verified.')
        return redirect('profile')
    
    # Check if verification is pending
    if user.verification_status == 'pending' and user.id_document:
        return render(request, 'users/verification_pending.html')
    
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.verification_status = 'pending'
            verification.verification_submitted_at = timezone.now()
            verification.save()
            
            messages.success(request, 'Your verification request has been submitted. You will be notified once approved.')
            return redirect('verification_pending')
    else:
        form = VerificationForm(instance=user)
    
    return render(request, 'users/verification_request.html', {'form': form})


@login_required
def verification_pending(request):
    """View for users with pending verification"""
    user = request.user
    
    if not user.id_document or not user.verification_status:
        return redirect('verification_request')
    
    if user.is_verified:
        messages.success(request, 'Your account is verified!')
        return redirect('profile')
    
    return render(request, 'users/verification_pending.html', {'user': user})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_verification_list(request):
    """Admin view to list verification requests"""
    pending_requests = CustomUser.objects.filter(
        verification_status='pending',
        id_document__isnull=False
    ).order_by('verification_submitted_at')
    
    processed_requests = CustomUser.objects.filter(
        verification_status__in=['approved', 'rejected'],
        id_document__isnull=False
    ).order_by('-verification_processed_at')[:50]  # Show last 50
    
    return render(request, 'users/admin_verification_list.html', {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def process_verification(request, user_id):
    """Admin view to approve/reject verification requests"""
    user_to_verify = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        user_to_verify.verification_notes = notes
        user_to_verify.verification_processed_at = timezone.now()
        
        if action == 'approve':
            user_to_verify.verification_status = 'approved'
            user_to_verify.is_verified = True
            messages.success(request, f"User {user_to_verify.username} has been verified.")
        elif action == 'reject':
            user_to_verify.verification_status = 'rejected'
            user_to_verify.is_verified = False
            messages.warning(request, f"Verification for {user_to_verify.username} has been rejected.")
        
        user_to_verify.save()
        return redirect('admin_verification_list')
    
    return render(request, 'users/process_verification.html', {
        'user_to_verify': user_to_verify
    })

@login_required
def premium_feature(request):
    if not request.user.is_verified:
        messages.warning(request, 'You must verify your account to access this feature.')
        return redirect('totp_setup')

    return render(request, 'users/premium_feature.html')


def landing_page(request):
    return render(request, 'users/landing.html')

@login_required
def totp_setup(request):
    """View for setting up TOTP-based two-factor authentication"""
    user = request.user
    
    # Check if user already has TOTP set up
    if user.totp_secret:
        messages.info(request, 'Two-factor authentication is already enabled for your account.')
        return redirect('profile')
    
    # Generate a new TOTP secret if not in session
    if 'totp_secret' not in request.session:
        request.session['totp_secret'] = pyotp.random_base32()
    
    secret = request.session['totp_secret']
    
    # Create QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user.email, issuer_name="YourSocialApp")
    
    img = qrcode.make(uri)
    buffered = BytesIO()
    img.save(buffered)
    qr_code = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    if request.method == 'POST':
        # Verify the entered code
        verification_code = request.POST.get('verification_code')
        if totp.verify(verification_code):
            # Save the secret to the user's profile
            user.totp_secret = secret
            user.save()
            
            # Clear the session secret
            if 'totp_secret' in request.session:
                del request.session['totp_secret']
            
            messages.success(request, 'Two-factor authentication has been successfully enabled for your account.')
            return redirect('profile')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
    
    return render(request, 'users/totp_setup.html', {
        'qr_code': qr_code,
        'secret': secret,
        'user': user
    })

def password_reset_request(request):
    """Request a password reset - requires email address"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Check if user has set up TOTP
                if not user.totp_secret:
                    messages.error(request, "You need to set up Two-Factor Authentication before you can reset your password.")
                    return redirect('login')
                
                # Create password reset request using the user's TOTP secret
                reset_request = PasswordResetRequest.objects.create(
                    user=user,
                    token=user.totp_secret,  # Use the existing TOTP secret
                    expires_at=timezone.now() + timezone.timedelta(minutes=10)
                )
                
                return redirect('password_reset_verify', reset_id=reset_request.id)
                
            except CustomUser.DoesNotExist:
                # Don't reveal if the email exists
                messages.warning(request, "If your email is registered and you have set up 2FA, you'll be redirected to the next step.")
                return redirect('login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_verify(request, reset_id):
    """Verify the TOTP code from the authenticator app"""
    reset_request = get_object_or_404(PasswordResetRequest, id=reset_id)
    
    # Check if reset request is valid
    if not reset_request.is_valid():
        messages.error(request, "This password reset link has expired or has been used.")
        return redirect('password_reset_request')
    
    user = reset_request.user
    
    # Ensure the user has TOTP set up
    if not user.totp_secret:
        messages.error(request, "You must set up Two-Factor Authentication before you can reset your password.")
        return redirect('login')
    
    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            
            # Verify the token against the user's TOTP secret
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(token):
                # Token is valid, allow setting new password
                request.session['reset_user_id'] = reset_request.user.id
                request.session['reset_request_id'] = reset_request.id
                return redirect('password_reset_confirm')
            else:
                messages.error(request, "Invalid authenticator code. Please try again.")
    else:
        form = PasswordResetVerifyForm()
    
    return render(request, 'users/password_reset_verify.html', {
        'form': form,
        'user': user
    })


def password_reset_confirm(request):
    """Set a new password after successful TOTP verification"""
    # Check if we have a valid reset in session
    reset_user_id = request.session.get('reset_user_id')
    reset_request_id = request.session.get('reset_request_id')
    
    if not reset_user_id or not reset_request_id:
        messages.error(request, "Invalid password reset session.")
        return redirect('password_reset_request')
    
    try:
        user = CustomUser.objects.get(id=reset_user_id)
        reset_request = PasswordResetRequest.objects.get(id=reset_request_id, user=user)
        
        # Check if reset request is still valid
        if not reset_request.is_valid():
            messages.error(request, "This password reset session has expired.")
            return redirect('password_reset_request')
        
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                # Set new password
                user.set_password(form.cleaned_data['password1'])
                user.save()
                
                # Mark reset request as used
                reset_request.is_used = True
                reset_request.save()
                
                # Clear session
                if 'reset_user_id' in request.session:
                    del request.session['reset_user_id']
                if 'reset_request_id' in request.session:
                    del request.session['reset_request_id']
                
                messages.success(request, "Your password has been changed successfully. You can now log in with your new password.")
                return redirect('login')
        else:
            form = SetNewPasswordForm()
        
        return render(request, 'users/password_reset_confirm.html', {'form': form})
    
    except (CustomUser.DoesNotExist, PasswordResetRequest.DoesNotExist):
        messages.error(request, "Invalid password reset session.")
        return redirect('password_reset_request')