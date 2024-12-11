from django.urls import path
from . import views

urlpatterns = [
    path('landing/', views.landing, name='landing'), 
    path('login/', views.login, name='login'), 
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('home/', views.home, name='home'),
    path('tracker/', views.tracker, name='tracker'),
    path('plan/', views.plan, name='plan'),
    path('program/', views.program, name='program'),
    path('me/', views.me, name='me'),
    path('personalinfo/', views.personalinfo, name='personalinfo'),
    path('accountinfo/', views.accountinfo, name='accountinfo'),
    path('logout/', views.logout_view, name='logout'),
    path('update_physiological_stats/', views.update_physiological_stats, name='update_physiological_stats'),
    path('submit_daily_survey/', views.submit_daily_survey, name='submit_daily_survey'),
    path('delete_account/', views.delete_account, name='delete_account'),
]
