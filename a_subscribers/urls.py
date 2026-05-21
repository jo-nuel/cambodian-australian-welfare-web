from django.urls import path

from . import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='newsletter_subscribe'),
    path('check-email/', views.check_email, name='newsletter_check_email'),
    path('confirm/<str:token>/', views.confirm, name='newsletter_confirm'),
    path('confirmed/', views.confirmed, name='newsletter_confirmed'),
    path('unsubscribe/<str:token>/', views.unsubscribe, name='newsletter_unsubscribe'),
    path('already-subscribed/', views.already_subscribed, name='newsletter_already_subscribed'),
]
