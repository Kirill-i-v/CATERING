from datetime import date
from threading import Thread
from time import sleep
from django.db.models import QuerySet
from food.models import Order
from food.enums import OrderStatus
from shared.cache import CacheService


class Processor:
    EXCLUDE_STATUSES = (
        OrderStatus.DELIVERED,
        OrderStatus.NOT_DELIVERED,
    )

    def __init__(self) -> None:
        self._thread = Thread(target=self.process, daemon=True)
        self.cache = CacheService()
        print(f"Orders Processor is created")

    @property
    def today(self):
        return date.today()

    def process(self):
        while True:
            self._process()
            sleep(2)

    def _process(self):
        for status in [OrderStatus.NOT_STARTED, OrderStatus.COOKING_REJECTED]:
            order_ids = self.cache.get("orders", status) or []
            if not order_ids:
                continue

            orders = Order.objects.filter(id__in=order_ids)
            for order in orders:
                match order.status:
                    case OrderStatus.NOT_STARTED:
                        self._process_not_started(order)
                    case OrderStatus.COOKING_REJECTED:
                        self._process_cooking_rejected()
                    case _:
                        print(f"Unrecognized order status: {order.status}. passing")

    def _update_cache(self, order_id: int, from_status: str, to_status: str):
        # Remove the old status
        old_list = self.cache.get("orders", from_status) or []
        if order_id in old_list:
            old_list.remove(order_id)
            self.cache.set("orders", from_status, old_list)

        # Add to new status
        new_list = self.cache.get("orders", to_status) or []
        new_list.append(order_id)
        self.cache.set("orders", to_status, new_list)

    def _process_not_started(self, order: Order):
        if order.eta > self.today:
            pass
        elif order.eta < self.today:
            order.status = OrderStatus.CANCELLED
            order.save()
            self._update_cache(order.pk, OrderStatus.NOT_STARTED, OrderStatus.CANCELLED)
            print(f"Cancelled order {order}")
        else:
            order.status = OrderStatus.COOKING
            order.save()
            self._update_cache(order.pk, OrderStatus.NOT_STARTED, OrderStatus.COOKING)
            restaurants = {item.dish.restaurant for item in order.items.all()}
            print(f"Finished preparing order. Restaurants: {restaurants}")
            print(f"Order: {order}")

    def _process_cooking_rejected(self):
        raise NotImplementedError
