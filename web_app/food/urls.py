from django.urls import path, re_path
from food import views

app_name = 'food'

DAY = r'(?P<day>\d{4}-\d{2}-\d{2})'

urlpatterns = [
    path('', views.home, name='home'),
    path('today/', views.open_today, name='open_today'),
    path('days/new/', views.new_day, name='new_day'),
    re_path(rf'^day/{DAY}/$', views.day_view, name='day'),
    re_path(rf'^day/{DAY}/values/$', views.day_values, name='day_values'),
    re_path(rf'^day/{DAY}/delete/$', views.delete_day, name='delete_day'),
]
