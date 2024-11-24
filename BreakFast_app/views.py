from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, LoginForm, CustomFastingPlanForm, PersonalInfoForm, AccountInfoForm, DailySurveyForm
from .models import User, UserProfile, FastingPlan, FastingTracker, WeightLog, DailySurvey
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
            # Create UserProfile for the new user
            UserProfile.objects.create(user=user)
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
    context = {}
    
    if request.user.is_authenticated:
        active_plan = FastingPlan.objects.filter(created_by=request.user, is_active=True).first()
        active_fast = FastingTracker.objects.filter(created_by=request.user, completed=False).first()
        
        # Get today's survey data
        today_survey = DailySurvey.objects.filter(
            user=request.user,
            date=timezone.now().date()
        ).first()
        
        context.update({
            'active_plan': active_plan,
            'active_fast': active_fast,
            'mood': today_survey.mood if today_survey else None,
            'energy': today_survey.energy_level if today_survey else None,
            'sleep_hours': today_survey.hours_of_sleep if today_survey else 0,
            'sleep_minutes': today_survey.minutes_of_sleep if today_survey else 0,
        })
        
        if active_fast:
            # Calculate progress circle offset
            if not active_fast.is_paused:
                total_duration = (active_fast.end_time - active_fast.start_time).total_seconds()
                elapsed = (timezone.now() - active_fast.start_time).total_seconds()
                progress = min(100, max(0, (elapsed / total_duration) * 100))
                context['circle_offset'] = 283 - (progress * 2.83)  # 283 is the circle's circumference
            else:
                context['circle_offset'] = 283  # Show empty circle when paused

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
                                end_time=end_time,
                                is_fasting=True  # Start with fasting window
                            )
                            messages.success(request, "Fasting started!")
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
                if active_fast:
                    sleep_hours = request.POST.get('sleep_hours')
                    sleep_minutes = request.POST.get('sleep_minutes')
                    
                    if sleep_hours is not None and sleep_minutes is not None:
                        try:
                            active_fast.sleep_hours = int(sleep_hours)
                            active_fast.sleep_minutes = int(sleep_minutes)
                            active_fast.save()
                            return JsonResponse({'status': 'success'})
                        except ValueError:
                            return JsonResponse({'status': 'error', 'message': 'Invalid sleep values'})
                    
                return JsonResponse({'status': 'error', 'message': 'Missing sleep values'})
            
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

        context['remaining_hours'] = remaining_hours
        context['progress_percentage'] = progress_percentage

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
                fasting_days=request.POST.get('fasting_days'),
                eating_days=request.POST.get('eating_days'),
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
                plan.is_preset = False  # Explicitly set is_preset to False for custom plans
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
    user_profile = request.user.userprofile
    today = timezone.now().date()
    current_month = timezone.now().strftime('%B %Y')
    
    # Get daily survey for today if it exists
    daily_survey = DailySurvey.objects.filter(user=request.user, date=today).first()
    
    # Get last 7 days of surveys
    recent_surveys = DailySurvey.objects.filter(
        user=request.user,
        date__gte=today - timezone.timedelta(days=7)
    ).order_by('-date')
    
    # Get recent weight logs
    weight_logs = WeightLog.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Get completed fasts count
    completed_fasts = FastingTracker.objects.filter(
        created_by=request.user,
        completed=True
    ).count()
    
    # Calendar data
    import calendar
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_days = cal.monthdatescalendar(today.year, today.month)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Get all fasting days in current month
    fasting_days = FastingTracker.objects.filter(
        created_by=request.user,
        start_time__year=today.year,
        start_time__month=today.month
    ).values_list('start_time__day', flat=True)
    
    # Process calendar data
    calendar_weeks = []
    for week in month_days:
        week_days = []
        for date in week:
            if date.month == today.month:
                week_days.append({
                    'day': date.day,
                    'is_today': date == today,
                    'has_fast': date.day in fasting_days,
                    'is_current_month': True
                })
            else:
                week_days.append({
                    'day': date.day,
                    'is_today': False,
                    'has_fast': False,
                    'is_current_month': False
                })
        calendar_weeks.append(week_days)
    
    context = {
        'user_profile': user_profile,
        'daily_survey': daily_survey,
        'recent_surveys': recent_surveys,
        'survey_form': DailySurveyForm() if not daily_survey else None,
        'weight_logs': weight_logs,
        'completed_fasts': completed_fasts,
        'current_month': current_month,
        'weekdays': weekdays,
        'calendar_weeks': calendar_weeks
    }
    
    return render(request, 'me.html', context)

@login_required
def submit_daily_survey(request):
    today = timezone.now().date()
    survey = DailySurvey.objects.filter(user=request.user, date=today).first()
    
    if request.method == 'POST':
        form = DailySurveyForm(request.POST, instance=survey)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.date = today
            survey.save()
            messages.success(request, 'Daily survey submitted successfully!')
            return JsonResponse({'status': 'success', 'redirect_url': reverse('me')})
        return JsonResponse({'status': 'error', 'errors': form.errors})
    
    form = DailySurveyForm(instance=survey)
    return render(request, 'daily_survey.html', {'form': form})

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
        try:
            stat_type = request.POST.get('type')
            value = request.POST.get('value')
            
            # Get or create today's survey
            survey, created = DailySurvey.objects.get_or_create(
                user=request.user,
                date=timezone.now().date()
            )
            
            if stat_type == 'mood':
                survey.mood = int(value)
            elif stat_type == 'energy':
                survey.energy_level = int(value)
            elif stat_type == 'sleep':
                hours = int(request.POST.get('hours', 0))
                minutes = int(request.POST.get('minutes', 0))
                survey.hours_of_sleep = hours
                survey.minutes_of_sleep = minutes
                
            survey.save()
            return JsonResponse({'status': 'success'})
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')

def logout_view(request):
    logout(request)
    return redirect('landing')  # Redirect to landing page after logout