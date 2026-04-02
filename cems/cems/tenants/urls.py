from django.urls import path
from . import views

urlpatterns = [
    path('', views.tenant_home, name='tenant_home'),
    path('register/', views.register_college, name='register_college'),
    path('<slug:slug>/', views.college_portal, name='college_portal'),
    path('<slug:slug>/login/', views.college_login, name='college_login'),
    path('<slug:slug>/register/', views.college_register, name='college_register'),
]

