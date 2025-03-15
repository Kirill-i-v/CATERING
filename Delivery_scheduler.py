import uuid
import random
import abc
import queue
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal


STORAGE = {
    "users": [],
    "dishes": [
        {"id": 1, "name": "pizza", "price": 1099, "restaurant": "Bueno"},
        {"id": 2, "name": "soda", "price": 199, "restaurant": "Melange"},
        {"id": 3, "name": "salad", "price": 599, "restaurant": "Melange"},
    ],
    "delivery": {},
}

OrderRequestBody = tuple[str, datetime]
DeliveryProvider = Literal["uber", "uklon"]


def blocking_process(delay):
    time.sleep(delay)


@dataclass
class DeliveryOrder:
    order_name: str
    number: uuid.UUID | None = None


class DeliveryService(abc.ABC):
    def __init__(self, order: DeliveryOrder) -> None:
        self._order: DeliveryOrder = order

    @classmethod
    def _process_delivery(cls) -> None:
        print(f"DELIVERY PROCESSING...")

        while True:
            delivery_items = STORAGE["delivery"]
            if not delivery_items:
                time.sleep(1)
                continue

            for key, value in delivery_items.items():
                if value[1] == "finished":
                    print(f"\n\t🚚 Order {key} is delivered by {value[0]} -> Marked as archived.")
                    STORAGE["delivery"][key][1] = "archived"
                    STORAGE["delivery"][key][2] = datetime.now()

            time.sleep(0.5)

    def _ship(self, delay: int):
        """All concrete .ship() MUST call this method!"""
        def callback():
            blocking_process(delay)
            STORAGE["delivery"][self._order.number][1] = "finished"
            STORAGE["delivery"][self._order.number][2] = datetime.now()
            print(f"\nUPDATED STORAGE: {self._order.number} is finished")

        thread = threading.Thread(target=callback)
        thread.start()

    @abc.abstractmethod
    def ship(self):
        """Concrete delivery provider implementation."""


class Uklon(DeliveryService):
    def ship(self):
        self._order.number = uuid.uuid4()
        STORAGE["delivery"][self._order.number] = ["uklon", "ongoing", datetime.now()]
        delay: int = random.randint(4, 8)
        print(f"\n🚚 Shipping [{self._order}] with Uklon. Time to wait: {delay}")
        self._ship(delay)


class Uber(DeliveryService):
    def ship(self):
        self._order.number = uuid.uuid4()
        STORAGE["delivery"][self._order.number] = ["uber", "ongoing", datetime.now()]
        delay: int = random.randint(1, 3)
        print(f"\n🚚 Shipping [{self._order}] with Uber. Time to wait: {delay}")
        self._ship(delay)


class Scheduler:
    def __init__(self):
        self.orders: queue.Queue[OrderRequestBody] = queue.Queue()

    def add_order(self, order: OrderRequestBody):
        self.orders.put(order)
        print(f"ORDER {order[0]} IS SCHEDULED")

    def _delivery_service_dispatcher(self) -> type[DeliveryService]:
        random_provider: DeliveryProvider = random.choice(("uklon", "uber"))
        match random_provider:
            case "uklon": return Uklon
            case "uber": return Uber
            case _: raise Exception("Unknown provider")

    def ship_order(self, order_name: str) -> None:
        service_class: type[DeliveryService] = self._delivery_service_dispatcher()
        service_class(order=DeliveryOrder(order_name=order_name)).ship()

    def process_orders(self):
        print("SCHEDULER PROCESSING...")
        while True:
            order = self.orders.get(True)
            time_to_wait = order[1] - datetime.now()
            if time_to_wait.total_seconds() > 0:
                self.orders.put(order)
                time.sleep(0.5)
            else:
                self.ship_order(order[0])


def cleanup_worker():
    print("CLEANUP WORKER STARTED...")
    while True:
        now = datetime.now()
        orders_to_remove = [
            order_id for order_id, details in STORAGE["delivery"].items()
            if details[1] == "archived" and (now - details[2]).total_seconds() > 60
        ]
        for order_id in orders_to_remove:
            del STORAGE["delivery"][order_id]
            print(f"\n🗑️ CLEANUP: Order {order_id} removed after 1 min")

        time.sleep(10)


def main():
    scheduler = Scheduler()

    threading.Thread(target=scheduler.process_orders, daemon=True).start()
    threading.Thread(target=DeliveryService._process_delivery, daemon=True).start()
    threading.Thread(target=cleanup_worker, daemon=True).start()

    while True:
        if order_details := input("Enter order details: "):
            data = order_details.split(" ")
            order_name, delay = data[0], int(data[1])
            scheduler.add_order((order_name, datetime.now() + timedelta(seconds=delay)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        raise SystemExit(0)