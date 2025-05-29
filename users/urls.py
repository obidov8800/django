# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views # views.py faylidan view funksiyalarini import qilish

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # Asosiy sahifa (home) loyihaning umumiy urls.py da bo'lishi yaxshiroq
    # Lekin hozircha bu yerda bo'lsin.
    path('home/', views.home_view, name='home'),
]