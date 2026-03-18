from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, Document, PrintConfiguration
from dashboard.models import PricingConfig
from decimal import Decimal

@login_required
def student_dashboard_view(request):
    if not request.user.is_student:
        return redirect('admin_dashboard')
        
    orders = request.user.orders.all().order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'orders/student_dashboard.html', context)

@login_required
def create_order_view(request):
    if not request.user.is_student:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        # 1. Handle File Upload
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            messages.error(request, 'Please upload a document.')
            return redirect('create_order')

        # 2. Get Form Data
        copies = int(request.POST.get('copies', 1))
        print_type = request.POST.get('print_type')
        sides = request.POST.get('sides')
        pages_selection = request.POST.get('pages_selection', 'all')
        
        # Determine number of pages (Mock logic for now, in a real app would parse the PDF)
        # Assuming 1 page for this demo unless specified in pages_selection
        # In actual implementation: PyPDF2 or similar to get page count
        estimated_pages = 1
        
        # 3. Calculate Cost
        pricing = PricingConfig.objects.first()
        if not pricing:
            pricing = PricingConfig.objects.create() # defaults
            
        cost_per_page = Decimal('0.00')
        if print_type == 'BW':
            if sides == 'Single':
                cost_per_page = pricing.bw_single_sided
            else:
                cost_per_page = pricing.bw_double_sided
        elif print_type == 'Color':
            if sides == 'Single':
                cost_per_page = pricing.color_single_sided
            else:
                cost_per_page = pricing.color_double_sided
                
        # Total cost logic
        total_sheets = estimated_pages 
        if sides == 'Double':
            total_sheets = (estimated_pages + 1) // 2
            
        estimated_cost = cost_per_page * total_sheets * copies
        
        # 4. Create Order & Document & Configuration
        order = Order.objects.create(user=request.user, total_cost=estimated_cost)
        document = Document.objects.create(order=order, file=uploaded_file, cost=estimated_cost)
        PrintConfiguration.objects.create(
            document=document,
            copies=copies,
            print_type=print_type,
            sides=sides,
            pages_selection=pages_selection
        )
        
        messages.success(request, 'Order created successfully. Please proceed to payment.')
        return redirect('checkout', order_id=order.id)
        
    pricing = PricingConfig.objects.first() or PricingConfig()
    return render(request, 'orders/create_order.html', {'pricing': pricing})

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
