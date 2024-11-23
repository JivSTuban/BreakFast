from django.contrib import admin
from .models import (
    FastingPlan,
    FastingTracker,
    UserProfile,
    WeightLog,
    Program,
    UserProgram
)

# Register your models here.

@admin.register(FastingPlan)
class FastingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'fasting_hours', 'eating_hours', 'is_preset', 'created_by')
    list_filter = ('is_preset', 'created_by')
    search_fields = ('name', 'description')

@admin.register(FastingTracker)
class FastingTrackerAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'plan', 'start_time', 'end_time', 'completed', 'is_paused')
    list_filter = ('completed', 'created_by', 'plan', 'is_paused')
    search_fields = ('created_by__email', 'notes')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_weight', 'target_weight', 'streak_count', 'total_fasts')
    search_fields = ('user__username',)

@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'body_fat', 'date')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'notes')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'difficulty', 'is_challenge')
    list_filter = ('difficulty', 'is_challenge')
    search_fields = ('name', 'description')

@admin.register(UserProgram)
class UserProgramAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'start_date', 'completed', 'progress')
    list_filter = ('completed', 'program', 'user')
    search_fields = ('user__username', 'program__name')
