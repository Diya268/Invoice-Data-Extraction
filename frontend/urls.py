from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.main_page, name='main-page'),
    path('', views.user_login, name='user-login'),
    path('register/', views.register_user, name='user-register'),
    path('profile/', views.user_profile, name='user-profile'),
    path('logout/', views.user_logout, name='user-logout'),

]




