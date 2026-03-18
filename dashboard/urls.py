from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('order/<uuid:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('settings/', views.settings_view, name='admin_settings'),
    path('users/', views.manage_users_view, name='manage_users'),
]
