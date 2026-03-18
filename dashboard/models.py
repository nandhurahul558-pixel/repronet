from django.db import models
from django.core.validators import MinValueValidator

class PricingConfig(models.Model):
    bw_single_sided = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, validators=[MinValueValidator(0)])
    bw_double_sided = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, validators=[MinValueValidator(0)])
    color_single_sided = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, validators=[MinValueValidator(0)])
    color_double_sided = models.DecimalField(max_digits=5, decimal_places=2, default=8.00, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pricing Config updated at {self.updated_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configurations"

class StoreSettings(models.Model):
    is_accepting_orders = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Accepting Orders: {self.is_accepting_orders}"

    class Meta:
        verbose_name = "Store Setting"
        verbose_name_plural = "Store Settings"
