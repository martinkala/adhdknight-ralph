from django.urls import path, re_path
from food import views

app_name = 'food'

DAY = r'(?P<day>\d{4}-\d{2}-\d{2})'
CATEGORY = r'(?P<category>[a-z_]+)'
ENTRY_ID = r'(?P<entry_id>[0-9A-Za-z-]{1,36})'
RECORD_ID = r'(?P<record_id>[0-9A-Za-z-]{1,36})'

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.day_list, name='list'),
    path('today/', views.open_today, name='open_today'),
    path('days/new/', views.new_day, name='new_day'),
    re_path(rf'^day/{DAY}/$', views.day_view, name='day'),
    re_path(rf'^day/{DAY}/values/$', views.day_values, name='day_values'),
    re_path(rf'^day/{DAY}/delete/$', views.delete_day, name='delete_day'),
    re_path(rf'^day/{DAY}/entries/{CATEGORY}/$', views.add_entries, name='add_entries'),
    re_path(rf'^day/{DAY}/entries/{CATEGORY}/{ENTRY_ID}/$', views.entry, name='entry'),
    re_path(rf'^day/{DAY}/entries/{CATEGORY}/{ENTRY_ID}/quantities/$', views.entry_quantities, name='entry_quantities'),
    path('suggestions/', views.suggestions, name='suggestions'),
    re_path(rf'^day/{DAY}/meds/$', views.add_meds, name='add_meds'),
    re_path(rf'^day/{DAY}/meds/move/$', views.move_med, name='move_med'),
    path('settings/meds/', views.meds_dictionary, name='meds_dictionary'),
    path('settings/meds/kind/', views.meds_dictionary_kind, name='meds_dictionary_kind'),
    path('settings/meds/delete/', views.meds_dictionary_delete, name='meds_dictionary_delete'),
    re_path(rf'^day/{DAY}/blood-pressures/$', views.add_blood_pressure, name='add_bp'),
    re_path(rf'^day/{DAY}/blood-pressures/{RECORD_ID}/$', views.blood_pressure, name='bp'),
    re_path(rf'^day/{DAY}/weights/$', views.add_weight, name='add_weight'),
    re_path(rf'^day/{DAY}/weights/{RECORD_ID}/$', views.weight, name='weight'),
]
