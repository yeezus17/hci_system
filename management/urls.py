from django.urls import path
from . import views # This imports from management/views.py

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='user_profile'),
    path('publier/', views.publier_annonce, name='publier_annonce'),
    path('annonces/', views.annonces_list, name='annonces_list'),
    path('annonces/<int:pk>/', views.annonce_detail, name='annonce_detail'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('services/', views.services_list, name='services_list'),
    path('services/publier/', views.create_service, name='create_service'),
    
]