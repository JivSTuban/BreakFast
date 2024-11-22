from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, LoginForm, CustomFastingPlanForm, PersonalInfoForm, AccountInfoForm
from .models import FastingPlan, FastingTracker, UserProfile, SleepLog
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                auth_login(request, user)
                # Get the next URL from POST data or GET parameters
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    # Get the next URL from GET parameters
    next_url = request.GET.get('next', '')
    return render(request, 'login.html', {'form': form, 'next': next_url})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set the backend for the user
            user.backend = 'BreakFast_app.backends.EmailBackend'
            auth_login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
        
    return render(request, 'signup.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def tracker(request):
    # Get active fast that is not completed and not paused
    active_fast = FastingTracker.objects.filter(
        created_by=request.user,
        completed=False,
    ).first()

    # Get the user's active plan
    active_plan = FastingPlan.objects.filter(
        created_by=request.user,
        is_active=True
    ).first()

    # Calculate remaining hours
    remaining_hours = 0
    if active_fast and not active_fast.is_paused:
        if active_fast.completed:
            remaining_hours = 0
        else:
            time_diff = active_fast.end_time - timezone.now()
            remaining_hours = time_diff.total_seconds() / 3600

    # Get latest sleep log
    latest_sleep = SleepLog.objects.filter(user=request.user).order_by('-wake_time').first()
    sleep_hours = 0
    sleep_minutes = 0
    if latest_sleep:
        duration = latest_sleep.wake_time - latest_sleep.sleep_time
        sleep_hours = duration.seconds // 3600
        sleep_minutes = (duration.seconds % 3600) // 60

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            if not active_fast:
                plan_id = request.POST.get('plan_id')
                if plan_id:  # Only proceed if plan_id is not empty
                    try:
                        plan = FastingPlan.objects.get(id=plan_id, is_active=True)
                        # Create new fasting tracker
                        if plan.plan_type == '5:2':
                            # For 5:2 diet, end time is end of day
                            end_time = timezone.now().replace(hour=23, minute=59, second=59)
                        else:
                            # For hourly-based plans
                            end_time = timezone.now() + timezone.timedelta(hours=plan.fasting_hours)
                        
                        active_fast = FastingTracker.objects.create(
                            created_by=request.user,
                            plan=plan,
                            start_time=timezone.now(),
                            end_time=end_time
                        )
                        messages.success(request, "Fasting started successfully!")
                    except FastingPlan.DoesNotExist:
                        messages.error(request, "Selected fasting plan not found or not active.")
                else:
                    messages.error(request, "Please select a fasting plan first.")
        
        elif action == 'stop':
            if active_fast:
                active_fast.completed = True
                active_fast.actual_end_time = timezone.now()
                active_fast.save()
                
                # Update user profile stats if it exists
                try:
                    profile = request.user.userprofile
                    profile.total_fasts += 1
                    current_duration = active_fast.get_duration().total_seconds() / 3600  # Convert to hours
                    profile.longest_fast = max(profile.longest_fast, current_duration)
                    profile.save()
                except UserProfile.DoesNotExist:
                    pass  # User profile doesn't exist
                messages.success(request, "Fasting stopped successfully!")
        
        elif action == 'pause':
            if active_fast and not active_fast.is_paused:
                active_fast.is_paused = True
                active_fast.pause_time = timezone.now()
                active_fast.save()
                messages.success(request, "Fasting paused!")
        
        elif action == 'resume':
            if active_fast and active_fast.is_paused:
                pause_duration = timezone.now() - active_fast.pause_time
                active_fast.end_time += pause_duration
                active_fast.is_paused = False
                active_fast.pause_time = None
                active_fast.save()
                messages.success(request, "Fasting resumed!")
        
        elif action == 'update_mood':
            if active_fast:
                mood = request.POST.get('mood')
                energy = request.POST.get('energy')
                if mood:
                    active_fast.mood = int(mood)
                if energy:
                    active_fast.energy_level = int(energy)
                active_fast.save()
                messages.success(request, "Mood and energy updated!")
        
        elif action == 'update_sleep':
            try:
                sleep_hours = int(request.POST.get('sleep_hours', 0))
                sleep_minutes = int(request.POST.get('sleep_minutes', 0))
                
                if 0 <= sleep_hours <= 23 and 0 <= sleep_minutes <= 59:
                    # Create a new sleep log
                    wake_time = timezone.now()
                    sleep_time = wake_time - timezone.timedelta(hours=sleep_hours, minutes=sleep_minutes)
                    
                    SleepLog.objects.create(
                        user=request.user,
                        sleep_time=sleep_time,
                        wake_time=wake_time,
                        quality=5  # Default quality, you can add this as a field in the form if needed
                    )
                    messages.success(request, "Sleep time logged successfully!")
                else:
                    messages.error(request, "Please enter valid sleep hours (0-23) and minutes (0-59).")
            except (ValueError, TypeError):
                messages.error(request, "Please enter valid numbers for sleep duration.")
        
        return redirect('tracker')

    # Calculate progress percentage for the timer circle
    progress_percentage = 0
    if active_fast and not active_fast.completed:
        if active_fast.is_paused:
            elapsed = active_fast.pause_time - active_fast.start_time
        else:
            elapsed = timezone.now() - active_fast.start_time
        total_duration = active_fast.end_time - active_fast.start_time
        progress_percentage = min(100, max(0, (elapsed.total_seconds() / total_duration.total_seconds()) * 100))

    context = {
        'active_fast': active_fast,
        'active_plan': active_plan,
        'remaining_hours': remaining_hours,
        'progress_percentage': progress_percentage,
        'sleep_hours': sleep_hours,
        'sleep_minutes': sleep_minutes,
    }
    return render(request, 'tracker.html', context)

@login_required
def plan(request):
    # Get existing plans
    user_plans = FastingPlan.objects.filter(created_by=request.user, is_preset=False)
    active_plan = FastingPlan.objects.filter(created_by=request.user, is_active=True).first()
    
    if request.method == 'POST':
        # Handle selecting an existing plan
        if 'select_plan' in request.POST:
            plan_id = request.POST.get('select_plan')
            try:
                # Deactivate all other plans
                FastingPlan.objects.filter(created_by=request.user, is_active=True).update(is_active=False)
                # Activate selected plan
                selected_plan = FastingPlan.objects.get(id=plan_id)
                selected_plan.is_active = True
                selected_plan.save()
                messages.success(request, f'{selected_plan.name} has been activated!')
                return redirect('tracker')
            except FastingPlan.DoesNotExist:
                messages.error(request, 'Selected plan not found.')
        
        # Handle preset plan selection
        elif 'plan_type' in request.POST:
            # Deactivate all other plans
            FastingPlan.objects.filter(created_by=request.user, is_active=True).update(is_active=False)
            
            # Create and activate new plan
            new_plan = FastingPlan.objects.create(
                name=request.POST.get('name'),
                plan_type=request.POST.get('plan_type'),
                fasting_hours=request.POST.get('fasting_hours'),
                eating_hours=request.POST.get('eating_hours'),
                description=request.POST.get('description'),
                created_by=request.user,
                is_preset=True,
                is_active=True
            )
            messages.success(request, f'{new_plan.name} has been activated!')
            return redirect('tracker')
        
        # Handle custom plan creation
        else:
            form = CustomFastingPlanForm(request.POST)
            if form.is_valid():
                # Deactivate all other plans
                FastingPlan.objects.filter(created_by=request.user, is_active=True).update(is_active=False)
                
                plan = form.save(commit=False)
                plan.created_by = request.user
                plan.is_preset = False
                plan.is_active = True
                plan.save()
                messages.success(request, 'Custom plan created and activated!')
                return redirect('tracker')
    else:
        form = CustomFastingPlanForm()

    context = {
        'user_plans': user_plans,
        'form': form,
        'active_plan': active_plan
    }
    return render(request, 'plan.html', context)

@login_required
def program(request):
    return render(request, 'program.html')

@login_required
def me(request):
    context = {
        'weekdays': ['Mon', 'Tues', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'dates': ['8', '9', '10', '11', '12', '13', '14'],
        'highlighted_date': '11'
    }
    return render(request, 'me.html', context)

@login_required
def landing(request):
    return render(request, 'landing.html')

@login_required
def personalinfo(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = PersonalInfoForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal information updated successfully!')
            return redirect('personalinfo')
    else:
        form = PersonalInfoForm(instance=request.user)
    
    return render(request, 'personalinfo.html', {'form': form})

@login_required
def accountinfo(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = AccountInfoForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account information updated successfully!')
            return redirect('accountinfo')
    else:
        form = AccountInfoForm(instance=profile)
    
    return render(request, 'accountinfo.html', {'form': form})

@login_required
def update_physiological_stats(request):
    if request.method == 'POST':
        active_fast = FastingTracker.objects.filter(
            created_by=request.user,
            completed=False
        ).first()

        if active_fast:
            mood = request.POST.get('mood')
            energy = request.POST.get('energy')
            
            if mood:
                active_fast.mood = int(mood)
            if energy:
                active_fast.energy_level = int(energy)
            
            active_fast.save()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_sleep_cycle(request):
    if request.method == 'POST':
        try:
            sleep_hours = int(request.POST.get('sleep_hours', 0))
            sleep_minutes = int(request.POST.get('sleep_minutes', 0))
            
            if 0 <= sleep_hours <= 23 and 0 <= sleep_minutes <= 59:
                wake_time = timezone.now()
                sleep_time = wake_time - timezone.timedelta(hours=sleep_hours, minutes=sleep_minutes)
                
                SleepLog.objects.create(
                    user=request.user,
                    sleep_time=sleep_time,
                    wake_time=wake_time,
                    quality=5  # Default quality
                )
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please enter valid sleep hours (0-23) and minutes (0-59).'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'Please enter valid numbers for sleep duration.'
            }, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

def logout_view(request):
    logout(request)
    return redirect('landing')  # Redirect to landing page after logout