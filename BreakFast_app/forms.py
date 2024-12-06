from django import forms
from .models import User, FastingPlan, FastingTracker, WeightLog, UserProfile, UserProgram, DailySurvey
import re
from django.utils import timezone

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists')
        
        # Username validation rules
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError('Username can only contain letters, numbers, and underscores')
        
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class CustomFastingPlanForm(forms.ModelForm):
    class Meta:
        model = FastingPlan
        fields = ['name', 'plan_type', 'fasting_hours', 'eating_hours', 'fasting_days', 'eating_days', 'description', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Plan Name', 'class': 'form-control'}),
            'plan_type': forms.Select(attrs={'class': 'form-control', 'id': 'plan_type'}),
            'fasting_hours': forms.NumberInput(attrs={'min': '1', 'max': '23', 'class': 'form-control', 'id': 'fasting_hours'}),
            'eating_hours': forms.NumberInput(attrs={'min': '1', 'max': '23', 'class': 'form-control', 'id': 'eating_hours'}),
            'fasting_days': forms.NumberInput(attrs={'min': '1', 'max': '6', 'class': 'form-control', 'id': 'fasting_days'}),
            'eating_days': forms.NumberInput(attrs={'min': '1', 'max': '6', 'class': 'form-control', 'id': 'eating_days'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Plan Description', 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        plan_type = cleaned_data.get('plan_type')
        fasting_hours = cleaned_data.get('fasting_hours')
        eating_hours = cleaned_data.get('eating_hours')
        fasting_days = cleaned_data.get('fasting_days')
        eating_days = cleaned_data.get('eating_days')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if plan_type == '5:2':
            # For 5:2 diet
            if not fasting_days or not eating_days:
                raise forms.ValidationError('Please specify both fasting and eating days for 5:2 diet')
            if fasting_days + eating_days != 7:
                raise forms.ValidationError('Fasting days and eating days must sum to 7')
            if fasting_days < 1 or fasting_days > 6:
                raise forms.ValidationError('Fasting days must be between 1 and 6')
            # Clear hourly fields for 5:2 diet
            cleaned_data['fasting_hours'] = None
            cleaned_data['eating_hours'] = None
        else:
            # For hourly-based plans
            if not fasting_hours or not eating_hours:
                raise forms.ValidationError('Please specify both fasting and eating hours')
            if fasting_hours + eating_hours != 24:
                raise forms.ValidationError('Fasting hours and eating hours must sum to 24')
            if fasting_hours < 1 or fasting_hours > 23:
                raise forms.ValidationError('Fasting hours must be between 1 and 23')
            # Clear daily fields for hourly plans
            cleaned_data['fasting_days'] = None
            cleaned_data['eating_days'] = None

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data

class MoodEnergyTrackerForm(forms.ModelForm):
    class Meta:
        model = FastingTracker
        fields = ['mood', 'energy_level', 'notes']
        widgets = {
            'mood': forms.Select(attrs={'class': 'form-control'}),
            'energy_level': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'How are you feeling today?'})
        }

class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['weight', 'body_fat', 'notes']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'body_fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Any notes about your measurements?'})
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['current_weight', 'target_weight', 'height', 'body_fat', 'preferred_theme']
        widgets = {
            'current_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'target_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'body_fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'preferred_theme': forms.Select(attrs={'class': 'form-control'}, 
                                         choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')])
        }

class ProgramEnrollmentForm(forms.ModelForm):
    class Meta:
        model = UserProgram
        fields = ['program', 'start_date']
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date < timezone.now().date():
            raise forms.ValidationError('Start date cannot be in the past')
        return start_date

class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'contact_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'})
        }

class AccountInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['current_weight', 'target_weight', 'height', 'body_fat', 'goal', 'activity_level']
        widgets = {
            'current_weight': forms.NumberInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'target_weight': forms.NumberInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'body_fat': forms.NumberInput(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'goal': forms.Select(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'}),
            'activity_level': forms.Select(attrs={'class': 'form-control', 'style': 'border: 1px solid #ddd; border-radius: 0.5rem; padding: 0.75rem;'})
        }

class DailySurveyForm(forms.ModelForm):
    class Meta:
        model = DailySurvey
        fields = ['hours_of_sleep', 'minutes_of_sleep', 'mood', 'energy_level', 'notes']
        widgets = {
            'hours_of_sleep': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '23',
                'placeholder': 'Hours'
            }),
            'minutes_of_sleep': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '59',
                'placeholder': 'Minutes'
            }),
            'mood': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'energy_level': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[(i, str(i)) for i in range(1, 6)]),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'How are you feeling today?'
            })
        }
