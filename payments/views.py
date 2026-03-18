import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .models import Transaction
from decimal import Decimal

# Initialize Razorpay Client (In a real app, use secrets from settings)
razorpay_client = razorpay.Client(auth=('rzp_test_YourKeyIdHere', 'rzp_test_YourSecretHere'))

@login_required
def checkout_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'Submitted':
        messages.info(request, "This order cannot be paid for in its current status.")
        return redirect('student_dashboard')

    # Convert amount to paise (1 INR = 100 paise)
    amount_in_paise = int(order.total_cost * 100)
    
    # Create Razorpay Order
    razorpay_order = razorpay_client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1'
    })
    
    # Create Transaction record
    transaction = Transaction.objects.create(
        order=order,
        amount=order.total_cost,
        razorpay_order_id=razorpay_order['id']
    )
    
    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': 'rzp_test_YourKeyIdHere',
        'amount': amount_in_paise,
        'currency': 'INR'
    }
    return render(request, 'orders/checkout.html', context)

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        try:
            transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
        except Transaction.DoesNotExist:
            return redirect('student_dashboard')
            
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        try:
            # Verify the signature
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # If successful
            transaction.status = 'SUCCESS'
            transaction.razorpay_payment_id = payment_id
            transaction.razorpay_signature = signature
            transaction.save()
            
            # Update order
            order = transaction.order
            order.status = 'In Queue'
            order.amount_paid = order.total_cost
            order.is_fully_paid = True
            order.save()
            
            messages.success(request, 'Payment successful. Your order is now in the queue.')
            return redirect('order_detail', order_id=order.id)
            
        except razorpay.errors.SignatureVerificationError:
            transaction.status = 'FAILED'
            transaction.save()
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('checkout', order_id=transaction.order.id)
            
    return redirect('student_dashboard')
