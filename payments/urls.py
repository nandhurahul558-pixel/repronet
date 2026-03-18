from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<uuid:order_id>/', views.checkout_view, name='checkout'),
    path('callback/', views.payment_callback, name='payment_callback'),
]
