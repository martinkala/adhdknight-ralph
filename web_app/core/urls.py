from django.urls import path
from core import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('trend/', views.trend, name='trend'),
    path('account/', views.account, name='account'),
    path('info/', views.info, name='info'),
]
