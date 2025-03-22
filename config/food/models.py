from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "restaurants"

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=50, null=True)
    price = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    class Meta:
        db_table = "dishes"
        verbose_name_plural = "Dishes"

    def __str__(self):
        return f"{self.name} - {self.price} ({self.restaurant})"

class DishesOrder(models.Model):
    external_order_id = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "dishes_orders"
        verbose_name_plural = "Dishes Orders"

    def __str__(self):
        return f"Order {self.external_order_id} by {self.user.username}"

class DishOrderItem(models.Model):
    quantity = models.SmallIntegerField()
    order = models.ForeignKey(DishesOrder, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)

    class Meta:
        db_table = "dish_order_items"

    def __str__(self):
        return f"{self.dish.name} x{self.quantity} (Order {self.order.external_order_id})"
