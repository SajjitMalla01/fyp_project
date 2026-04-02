from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/edit/', views.event_update, name='event_update'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/approve/', views.approve_event, name='approve_event'),
    path('events/<int:pk>/publish/', views.publish_event, name='publish_event'),
    path('events/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('api/event/<int:pk>/update-status/', views.update_event_status, name='update_event_status'),
]