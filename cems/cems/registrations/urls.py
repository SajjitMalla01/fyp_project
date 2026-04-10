from django.urls import path
from registrations import views

urlpatterns = [
    path('dashboard/', views.my_registrations, name='registrations_old'),
    path('event/<int:event_id>/register/', views.register_event, name='register_event'),
    path('<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('event/<int:event_id>/participants/', views.participant_list, name='participant_list'),
    path('verify/<int:registration_id>/', views.verify_registration, name='verify_registration'),
    path('<int:registration_id>/approve/', views.approve_registration, name='approve_registration'),
    path('<int:registration_id>/reject/', views.reject_registration, name='reject_registration'),
    path('scanner/', views.scanner_view, name='scanner'),
]