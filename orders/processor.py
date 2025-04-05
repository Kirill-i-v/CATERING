from datetime import date
from threading import Thread
from time import sleep
import json
from django.db.models import QuerySet
from shared.cache import CacheService
from food.models import Order
from food.enums import OrderStatus


class Processor:
    EXCLUDE_STATUSES = (
        OrderStatus.DELIVERED,
        OrderStatus.NOT_DELIVERED,
    )

    def __init__(self) -> None:
        self._thread = Thread(target=self.process, daemon=True)
        self.cache = CacheService()
        print("Orders Processor is created")

    @property
    def today(self):
        return date.today()

    def start(self):
        self._thread.start()
        print("Orders Processor started processing orders")

    def process(self):
        while True:
            try:
                self._process()
            except Exception as e:
                print(f"[Processor Error] {e}")
            sleep(2)

    def _process(self):
        keys = self.cache.connection.keys("orders_processing:order:*")
        print(f"[Processor] Found {len(keys)} order(s) in cache")

        for key in keys:
            raw = self.cache.connection.get(key)
            if not raw:
                continue

            try:
                order_data = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[Processor] Invalid JSON for key {key}, deleting it")
                self.cache.connection.delete(key)
                continue

            status = order_data.get("status")
            eta_str = order_data.get("eta")
            order_id = order_data.get("id")

            if not status or not eta_str or not order_id:
                print(f"[Processor] Missing data in cache for order {key}, skipping")
                continue

            eta = date.fromisoformat(eta_str)

            match status:
                case OrderStatus.NOT_STARTED:
                    self._process_not_started(order_data, eta)
                case OrderStatus.COOKING_REJECTED:
                    self._process_cooking_rejected()
                case _:
                    print(f"[Processor] Unrecognized status {status}, skipping")

    def _process_not_started(self, order_data: dict, eta: date):
        order_id = order_data["id"]

        if eta > self.today:
            return  # Future order – do nothing

        elif eta < self.today:
            # Expired ETA – cancel
            Order.objects.filter(pk=order_id).update(status=OrderStatus.CANCELLED)
            print(f"[Processor] Cancelled expired order {order_id}")
            self.cache.delete("orders_processing", f"order:{order_id}")

        else:
            # ETA is today – begin cooking
            Order.objects.filter(pk=order_id).update(status=OrderStatus.COOKING)
            restaurant_ids = {item["restaurant_id"] for item in order_data["items"]}
            print(f"[Processor] Order {order_id} is now COOKING")
            print(f"[Processor] Involved restaurants: {restaurant_ids}")
            self.cache.delete("orders_processing", f"order:{order_id}")

    def _process_cooking_rejected(self):
        raise NotImplementedError
