from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.student_login_view, name='student_login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
]
