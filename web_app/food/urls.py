from django.urls import path
from food import views

app_name = 'food'

urlpatterns = [
    path('', views.home, name='home'),
]
