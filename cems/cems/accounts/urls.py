from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('register/<slug:college_slug>/', views.register, name='register_college_scoped'),
    path('login/', views.login_view, name='login'),
    path('login/<slug:college_slug>/', views.login_view, name='login_college_scoped'),
    path('admin-gateway/', views.admin_gateway, name='admin_gateway'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('switch-college/<uuid:college_id>/', views.switch_college, name='switch_college'),
]