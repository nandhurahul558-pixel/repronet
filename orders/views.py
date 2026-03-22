from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Order, Document, PrintConfiguration
from dashboard.models import PricingConfig
from decimal import Decimal
import os

def get_pdf_page_count(file_path):
    """Get the number of pages in a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception:
        return 1  # Default to 1 if unable to read

def parse_page_selection(pages_selection, total_pages):
    """
    Parse page selection string and return list of pages to print.
    Supports: 'all', '1-5', '1,3,5-7', etc.
    Returns tuple: (selected_pages_list, page_count)
    """
    if pages_selection.strip().lower() == 'all':
        return list(range(1, total_pages + 1)), total_pages
    
    pages = []
    try:
        parts = pages_selection.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                pages.extend(range(start, min(end + 1, total_pages + 1)))
            else:
                page_num = int(part)
                if 1 <= page_num <= total_pages:
                    pages.append(page_num)
        
        return sorted(list(set(pages))), len(set(pages))
    except (ValueError, AttributeError):
        return list(range(1, total_pages + 1)), total_pages

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
        # 1. Handle File Upload (single + multiple input compatibility)
        uploaded_files = request.FILES.getlist('documents')
        if not uploaded_files:
            single_file = request.FILES.get('document')
            if single_file:
                uploaded_files = [single_file]

        if not uploaded_files:
            messages.error(request, 'Please upload at least one document.')
            return redirect('create_order')

        # 2. Get Form Data
        copies = int(request.POST.get('copies', 1))
        print_type = request.POST.get('print_type')
        sides = request.POST.get('sides')
        pages_selection = request.POST.get('pages_selection', 'all').strip() or 'all'
        if len(uploaded_files) > 1 and pages_selection.lower() != 'all':
            pages_selection = 'all'
            messages.warning(request, 'Page range is only supported for single document orders. Using all pages for multiple documents.')
        
        # 4. Calculate Cost
        pricing = PricingConfig.objects.first()
        if not pricing:
            pricing = PricingConfig.objects.create()  # defaults
            
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
                
        # 5. Create Order, then add each Document + Configuration
        order = Order.objects.create(user=request.user, total_cost=Decimal('0.00'))
        estimated_cost = Decimal('0.00')
        total_documents = 0
        total_detected_pages = 0
        total_print_pages = 0

        import tempfile
        for uploaded_file in uploaded_files:
            temp_path = None
            try:
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                total_pages = get_pdf_page_count(temp_path)
            except Exception:
                total_pages = 1
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            uploaded_file.seek(0)
            _, actual_pages = parse_page_selection(pages_selection, total_pages)

            total_sheets = actual_pages
            if sides == 'Double':
                total_sheets = (actual_pages + 1) // 2

            document_cost = cost_per_page * total_sheets * copies
            estimated_cost += document_cost
            total_documents += 1
            total_detected_pages += total_pages
            total_print_pages += actual_pages

            document = Document.objects.create(
                order=order,
                file=uploaded_file,
                cost=document_cost,
                total_pages=total_pages
            )
            PrintConfiguration.objects.create(
                document=document,
                copies=copies,
                print_type=print_type,
                sides=sides,
                pages_selection=pages_selection
            )

        order.total_cost = estimated_cost
        order.save(update_fields=['total_cost', 'updated_at'])

        messages.success(
            request,
            f'Order created successfully with {total_documents} document(s). Total pages: {total_detected_pages}, pages to print: {total_print_pages}.'
        )
        return redirect('checkout', order_id=order.id)
        
    pricing = PricingConfig.objects.first() or PricingConfig()
    return render(request, 'orders/create_order.html', {'pricing': pricing})

@login_required
def calculate_cost_ajax(request):
    """AJAX endpoint to calculate cost in real-time"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        total_pages = int(data.get('total_pages', 1))
        pages_selection = data.get('pages_selection', 'all')
        copies = int(data.get('copies', 1))
        print_type = data.get('print_type', 'BW')
        sides = data.get('sides', 'Single')
        
        # Parse page selection
        selected_pages, actual_pages = parse_page_selection(pages_selection, total_pages)
        
        # Get pricing
        pricing = PricingConfig.objects.first() or PricingConfig()
        
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
        
        total_sheets = actual_pages
        if sides == 'Double':
            total_sheets = (actual_pages + 1) // 2
        
        estimated_cost = float(cost_per_page * total_sheets * copies)
        
        return JsonResponse({
            'actual_pages': actual_pages,
            'total_sheets': total_sheets,
            'estimated_cost': estimated_cost,
            'cost_per_page': float(cost_per_page)
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def detect_pdf_pages_ajax(request):
    """AJAX endpoint to detect PDF page count when file is uploaded"""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        # Save file temporarily to detect pages
        import tempfile
        temp_path = None
        try:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            total_pages = get_pdf_page_count(temp_path)
            
            return JsonResponse({
                'success': True,
                'total_pages': total_pages,
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'total_pages': 1
            }, status=400)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
