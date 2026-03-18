import razorpay
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .models import Transaction

logger = logging.getLogger(__name__)


def get_razorpay_client():
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

    if not key_id or not key_secret:
        return None, None

    return razorpay.Client(auth=(key_id, key_secret)), key_id

@login_required
def checkout_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    razorpay_client, razorpay_key_id = get_razorpay_client()

    if razorpay_client is None:
        messages.error(request, "Payment gateway is not configured. Please contact admin.")
        return redirect('order_detail', order_id=order.id)
    
    if order.status != 'Submitted':
        messages.info(request, "This order cannot be paid for in its current status.")
        return redirect('student_dashboard')

    # Convert amount to paise (1 INR = 100 paise)
    amount_in_paise = int(order.total_cost * 100)
    
    # Create Razorpay Order
    try:
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1,
        })
    except razorpay.errors.BadRequestError:
        logger.exception("Razorpay order creation failed for order %s", order.id)
        messages.error(request, "Unable to initialize payment. Please verify gateway credentials.")
        return redirect('order_detail', order_id=order.id)
    
    # Create Transaction record
    transaction = Transaction.objects.create(
        order=order,
        amount=order.total_cost,
        razorpay_order_id=razorpay_order['id']
    )
    
    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': razorpay_key_id,
        'amount': amount_in_paise,
        'currency': 'INR'
    }
    return render(request, 'orders/checkout.html', context)

@csrf_exempt
def payment_callback(request):
    razorpay_client, _ = get_razorpay_client()

    if razorpay_client is None:
        messages.error(request, "Payment gateway is not configured. Please contact admin.")
        return redirect('student_dashboard')

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
        except razorpay.errors.BadRequestError:
            transaction.status = 'FAILED'
            transaction.save()
            logger.exception("Razorpay callback failed for order %s", transaction.order.id)
            messages.error(request, 'Payment provider rejected the callback. Please retry payment.')
            return redirect('checkout', order_id=transaction.order.id)
            
    return redirect('student_dashboard')
