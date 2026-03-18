from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('create/', views.create_order_view, name='create_order'),
    path('<uuid:order_id>/', views.order_detail_view, name='order_detail'),
]
