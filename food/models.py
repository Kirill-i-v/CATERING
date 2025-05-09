from django.conf import settings
from django.db import models
from .constants import RESTAURANT_TO_INTERNAL_STATUSES
from .enums import OrderStatus
from .enums import Restaurant as RestaurantEnum



class Restaurant(models.Model):
    class Meta:
        db_table = "restaurants"

    name = models.CharField(max_length=100, blank=False)
    address = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:
        return f"[{self.pk}] {self.name}"


class Dish(models.Model):
    class Meta:
        db_table = "dishes"
        verbose_name_plural = "dishes"

    name = models.CharField(max_length=50, null=True)
    price = models.IntegerField()
    restaurant = models.ForeignKey("Restaurant", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name} {self.price}  ({self.restaurant})"


class Order(models.Model):

    class Meta:
        db_table = "orders"

    status = models.CharField(max_length=20)
    provider = models.CharField(max_length=20, null=True, blank=True)
    eta = models.DateField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.pk} {self.status} for {self.user.email}"

    def __repr__(self) -> str:
        return super().__str__()

    @classmethod
    def update_from_provider_status(cls, id_: int, status: str, delivery=False) -> None:
        if delivery is False:
            if status == "finished":
                cls.objects.filter(id=id_).update(status=OrderStatus.DRIVER_LOOKUP)
            else:
                cls.objects.filter(id=id_).update(
                    status=RESTAURANT_TO_INTERNAL_STATUSES[RestaurantEnum.MELANGE][
                        status
                    ]
                )
        else:
            if status == "delivered":
                cls.objects.filter(id=id_).update(status=OrderStatus.DELIVERED)
            elif status == "delivery":
                cls.objects.filter(id=id_).update(status=OrderStatus.DELIVERY)
            elif status == "delivered":
                cls.objects.filter(id=id_).update(status=OrderStatus.DELIVERED)
            else:
                raise ValueError(f"Status {status} is not supported")


class DishOrderItem(models.Model):
    class Meta:
        db_table = "dish_order_items"

    quantity = models.SmallIntegerField()
    dish = models.ForeignKey("Dish", on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="items")

    def __str__(self) -> str:
        return f"[{self.order.pk}] {self.dish.name}: {self.quantity}"


class ExternalOrder(models.Model):
    class Meta:
        db_table = "external_orders"

    provider = models.CharField(max_length=20)
    external_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="external_orders")

    def __str__(self):
        return f"{self.provider} - {self.external_id}: {self.status}"
