from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    
    # def __str__(self):
    #     return self.username

class FastingPlan(models.Model):
    PLAN_TYPES = [
        ('16:8', '16:8 Intermittent Fasting'),
        ('18:6', '18:6 Intermittent Fasting'),
        ('20:4', '20:4 Intermittent Fasting'),
        ('5:2', '5:2 Diet'),
        ('CUSTOM', 'Custom Plan')
    ]
    
    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    fasting_hours = models.IntegerField(null=True, blank=True)
    eating_hours = models.IntegerField(null=True, blank=True)
    fasting_days = models.IntegerField(null=True, blank=True)  # For 5:2 diet
    eating_days = models.IntegerField(null=True, blank=True)   # For 5:2 diet
    description = models.TextField(blank=True)
    is_preset = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.plan_type == '5:2' and self.fasting_days and self.eating_days:
            return f"{self.name} ({self.fasting_days}:{self.eating_days} days)"
        return f"{self.name} ({self.fasting_hours}:{self.eating_hours} hours)"

class FastingTracker(models.Model):
    MOOD_CHOICES = [
        (1, 'Very Bad'),
        (2, 'Bad'),
        (3, 'Neutral'),
        (4, 'Good'),
        (5, 'Very Good')
    ]
    
    ENERGY_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Medium'),
        (4, 'High'),
        (5, 'Very High')
    ]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(FastingPlan, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)
    mood = models.IntegerField(choices=MOOD_CHOICES, null=True, blank=True)
    energy_level = models.IntegerField(choices=ENERGY_CHOICES, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)  # In case user ends early
    is_paused = models.BooleanField(default=False)
    pause_time = models.DateTimeField(null=True, blank=True)
    is_fasting = models.BooleanField(default=True)  # True for fasting window, False for eating window

    # Exercise tracking
    exercise_duration = models.IntegerField(help_text="Exercise duration in minutes", null=True, blank=True)
    water_intake = models.FloatField(help_text="Water intake in liters", null=True, blank=True)

    def __str__(self):
        return f"{self.created_by.email}'s fast - {self.start_time.date()}"

    def get_duration(self):
        if self.completed and self.actual_end_time:
            return self.actual_end_time - self.start_time
        if self.is_paused:
            return self.pause_time - self.start_time
        return timezone.now() - self.start_time

    def get_progress(self):
        if self.completed:
            return 100
        if self.is_paused:
            total_duration = self.end_time - self.start_time
            elapsed_duration = self.pause_time - self.start_time
        else:
            total_duration = self.end_time - self.start_time
            elapsed_duration = timezone.now() - self.start_time
        progress = (elapsed_duration.total_seconds() / total_duration.total_seconds()) * 100
        return min(100, max(0, progress))

class UserProfile(models.Model):
    GOAL_CHOICES = [
        ('WEIGHT_LOSS', 'Weight Loss'),
        ('MUSCLE_GAIN', 'Muscle Gain'),
        ('MAINTENANCE', 'Maintenance'),
        ('HEALTH', 'Overall Health'),
        ('ENERGY', 'Energy Management')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_weight = models.FloatField(null=True, blank=True)
    target_weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    preferred_theme = models.CharField(max_length=20, default='light')
    streak_count = models.IntegerField(default=0)
    total_fasts = models.IntegerField(default=0)
    longest_fast = models.IntegerField(default=0)  # in hours
    
    # New fields for enhanced tracking
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='HEALTH')
    activity_level = models.CharField(max_length=20, choices=[
        ('SEDENTARY', 'Sedentary'),
        ('LIGHT', 'Lightly Active'),
        ('MODERATE', 'Moderately Active'),
        ('VERY', 'Very Active'),
        ('EXTRA', 'Extra Active')
    ], default='MODERATE')
    notifications_enabled = models.BooleanField(default=True)
    fasting_reminder_time = models.TimeField(null=True, blank=True)
    measurement_reminder_day = models.IntegerField(choices=[(i, i) for i in range(1, 8)], default=1)  # Day of week
    badges_earned = models.JSONField(default=dict)
    achievements = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_bmi(self):
        if self.current_weight and self.height:
            return round(self.current_weight / ((self.height/100) ** 2), 2)
        return None

    def update_streak(self, completed_fast=True):
        if completed_fast:
            self.streak_count += 1
            self.total_fasts += 1
        else:
            self.streak_count = 0
        self.save()

class Program(models.Model):
    DIFFICULTY_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField()  # in days
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    is_challenge = models.BooleanField(default=False)
    
    # New fields for enhanced program features
    daily_tasks = models.JSONField(default=list)
    rewards = models.JSONField(default=dict)
    prerequisites = models.TextField(null=True, blank=True)
    tips = models.JSONField(default=list)
    resources = models.JSONField(default=list)
    success_stories = models.JSONField(default=list)

    def __str__(self):
        return self.name

    def get_completion_rate(self):
        total_users = UserProgram.objects.filter(program=self).count()
        completed_users = UserProgram.objects.filter(program=self, completed=True).count()
        return round((completed_users / total_users * 100) if total_users > 0 else 0, 2)

class UserProgram(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    start_date = models.DateField()
    completed = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)  # percentage

    def __str__(self):
        return f"{self.user.username} - {self.program.name}"

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField()
    weight_change = models.FloatField(null=True, blank=True)  # Added field for weight change
    body_fat = models.FloatField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.date}"

class DailySurvey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    hours_of_sleep = models.FloatField(null=True, blank=True)
    minutes_of_sleep = models.IntegerField(null=True, blank=True)
    mood = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    energy_level = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email}'s survey on {self.date}"
