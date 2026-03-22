from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('create/', views.create_order_view, name='create_order'),
    path('api/detect-pages/', views.detect_pdf_pages_ajax, name='detect_pages'),
    path('api/calculate-cost/', views.calculate_cost_ajax, name='calculate_cost'),
    path('<uuid:order_id>/', views.order_detail_view, name='order_detail'),
]
