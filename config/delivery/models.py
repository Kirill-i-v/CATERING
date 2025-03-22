from django.db import models
from food.models import DishesOrder

PROVIDERS_CHOICES = (
    ("uklon", "Uklon"),
    ("uber", "Uber"),
)

DELIVERY_STATUSES_CHOICES = (
    ("not started", "Not started"),
    ("ongoing", "Ongoing"),
    ("cancelled", "Cancelled"),
    ("done", "Successfully finished"),
    ("stolen", "Stolen"),
)


class DeliveryDishesOrder(models.Model):
    provider = models.CharField(max_length=100, choices=PROVIDERS_CHOICES)
    status = models.CharField(max_length=50, choices=DELIVERY_STATUSES_CHOICES)
    addresses = models.TextField()
    external_order_id = models.CharField(max_length=255)
    order = models.ForeignKey(DishesOrder, on_delete=models.CASCADE)

    class Meta:
        db_table = "dishes_orders_deliveries"

    def __str__(self):
        return f"Delivery {self.external_order_id} ({self.get_status_display()})"

