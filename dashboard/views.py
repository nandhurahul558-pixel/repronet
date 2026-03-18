from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import PricingConfig, StoreSettings
from orders.models import Order
from accounts.models import User
from decimal import Decimal

def is_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_superuser)

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    today = timezone.now().date()
    
    # Metrics
    daily_orders = Order.objects.filter(created_at__date=today)
    total_orders_today = daily_orders.count()
    revenue_today = sum(order.total_cost for order in daily_orders if order.is_fully_paid)
    
    pending_jobs = Order.objects.filter(status__in=['Submitted', 'In Queue']).count()
    printing_jobs = Order.objects.filter(status='Printing').count()
    completed_jobs = Order.objects.filter(status='Completed').count()
    
    # All active orders for table
    active_orders = Order.objects.exclude(status='Completed').order_by('-created_at')
    
    context = {
        'total_orders_today': total_orders_today,
        'revenue_today': revenue_today,
        'pending_jobs': pending_jobs,
        'printing_jobs': printing_jobs,
        'completed_jobs': completed_jobs,
        'active_orders': active_orders,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@user_passes_test(is_admin)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order {order.id} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def settings_view(request):
    pricing = PricingConfig.objects.first()
    if not pricing:
        pricing = PricingConfig.objects.create()
        
    store_settings = StoreSettings.objects.first()
    if not store_settings:
        store_settings = StoreSettings.objects.create()

    if request.method == 'POST':
        if 'update_pricing' in request.POST:
            pricing.bw_single_sided = Decimal(request.POST.get('bw_single_sided', pricing.bw_single_sided))
            pricing.bw_double_sided = Decimal(request.POST.get('bw_double_sided', pricing.bw_double_sided))
            pricing.color_single_sided = Decimal(request.POST.get('color_single_sided', pricing.color_single_sided))
            pricing.color_double_sided = Decimal(request.POST.get('color_double_sided', pricing.color_double_sided))
            pricing.save()
            messages.success(request, 'Pricing updated successfully.')
            
        elif 'toggle_service' in request.POST:
            store_settings.is_accepting_orders = not store_settings.is_accepting_orders
            store_settings.save()
            messages.success(request, f"Service toggled. Accepting orders: {store_settings.is_accepting_orders}")
            
        return redirect('admin_settings')

    context = {
        'pricing': pricing,
        'store_settings': store_settings,
    }
    return render(request, 'dashboard/settings.html', context)

@user_passes_test(is_admin)
def manage_users_view(request):
    students = User.objects.filter(is_student=True)
    return render(request, 'dashboard/manage_users.html', {'students': students})
