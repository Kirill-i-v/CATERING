from django.db import models
from users.models import User
from restaurants.models import Dish


class Order(models.Model):
    external_order_id = models.CharField(max_length=255)

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class DishOrder(models.Model):
    # class Meta:

    #     db_table = "custom_table_name"

    quantity = models.SmallIntegerField()

    order = models.ForeignKey("Order", on_delete=models.CASCADE)

    dish = models.ForeignKey("restaurants.Dish", on_delete=models.CASCADE)


class DeliveryOrder(models.Model):
    provider = models.CharField(max_length=100)

    status = models.CharField(max_length=50)

    addresses = models.TextField()

    external_order_id = models.CharField(max_length=255)

    order = models.ForeignKey("Order", on_delete=models.CASCADE)

