from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('In Queue', 'In Queue'),
        ('Printing', 'Printing'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Payment status tracking (useful for partial payments)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_fully_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} ({self.status})"

class Document(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Computed cost for this specific document
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Doc {self.id} for Order {self.order.id}"

class PrintConfiguration(models.Model):
    PRINT_TYPE_CHOICES = [
        ('BW', 'Black & White'),
        ('Color', 'Color'),
    ]
    SIDES_CHOICES = [
        ('Single', 'Single Sided'),
        ('Double', 'Double Sided'),
    ]

    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='configuration')
    copies = models.PositiveIntegerField(default=1)
    print_type = models.CharField(max_length=10, choices=PRINT_TYPE_CHOICES, default='BW')
    sides = models.CharField(max_length=10, choices=SIDES_CHOICES, default='Single')
    pages_selection = models.CharField(max_length=100, default='all', help_text="e.g., 'all', '1-5', '1,3,5-7'")

    def __str__(self):
        return f"Config for Doc {self.document.id}: {self.copies}x {self.print_type} {self.sides}"
