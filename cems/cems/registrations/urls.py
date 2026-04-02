from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.registrations_old, name='registrations_old'),
    path('event/<int:event_id>/register/', views.register_event, name='register_event'),
    path('<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('event/<int:event_id>/participants/', views.participant_list, name='participant_list'),
]