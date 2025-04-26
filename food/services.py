from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from time import sleep
from typing import Any
import random
from config import celery_app
from shared.cache import CacheService

from .enums import OrderStatus, Restaurant
from .models import DishOrderItem, Order
from .providers import bueno, melange, uklon, uber


@dataclass
class OrderInCache:
    restaurants: dict = field(default_factory=defaultdict)
    location: tuple[float, float] | None = None

    def append(self, restaurant: str, item: DishOrderItem):
        if not self.restaurants.get(restaurant, None):
            self.restaurants[restaurant] = {
                "external_id": None,
                "status": "not started",
                "address": item.dish.restaurant.address,
                "dishes": [
                    {
                        "dish": item.dish.name,
                        "quantity": item.quantity,
                    }
                ],
            }
        else:
            self.restaurants[restaurant]["dishes"].append(
                {
                    "dish": item.dish.name,
                    "quantity": item.quantity,
                }
            )


def all_orders_cooked(order: OrderInCache) -> bool:
    flag = True

    for rest, _order in order.restaurants.items():
        if rest == Restaurant.MELANGE:
            if _order["status"] not in (
                melange.OrderStatus.COOKED,
                melange.OrderStatus.FINISHED,
            ):
                flag = False
                break
        elif rest == Restaurant.BUENO:
            if _order["status"] not in (
                bueno.OrderStatus.COOKED,
                bueno.OrderStatus.FINISHED,
            ):
                flag = False
                break

    # note: must be done not there
    # if flag is True:
    #     Order.update_from_provider_status(
    #         id_=order.internal_order_id, status="finished"
    #     )

    return flag


@celery_app.task
def melange_order_processing(internal_order_id: int):
    provider = melange.Provider()
    cache = CacheService()

    cooked = False
    while not cooked:
        sleep(1)
        order_in_cache = OrderInCache(
            **cache.get(namespace="orders", key=internal_order_id)
        )
        melange_order: dict[str, Any] | None = order_in_cache.restaurants.get(
            Restaurant.MELANGE
        )
        if not melange_order:
            break

        print(f"MELANGE ORDER STATUS: {melange_order['status']}")

        if melange_order["status"] == melange.OrderStatus.NOT_STARTED:
            if not melange_order["external_id"]:
                response: melange.OrderResponse = provider.create_order(
                    melange.OrderRequestBody(
                        order=[
                            melange.OrderItem(**item)
                            for item in melange_order["dishes"]
                        ]
                    )
                )
                # update cache
                order_in_cache.restaurants[Restaurant.MELANGE][
                    "external_id"
                ] = response.id
                # skip database update, since "not started" is default value
            else:
                response: melange.OrderResponse = provider.get_order(
                    order_id=melange_order["external_id"]
                )

                if melange_order["status"] != response.status:  # status changed
                    order_in_cache.restaurants[Restaurant.MELANGE][
                        "status"
                    ] = response.status

                sleep(1)
        elif melange_order["status"] == melange.OrderStatus.COOKING:
            response = provider.get_order(order_id=melange_order["external_id"])
            print(f"\t RESPONSE STATUS: {response.status}")

            if melange_order["status"] != response.status:  # if status changed
                order_in_cache.restaurants[Restaurant.MELANGE][
                    "status"
                ] = response.status
            sleep(1)
        elif melange_order["status"] in (
            melange.OrderStatus.COOKED,
            melange.OrderStatus.FINISHED,
        ):
            cooked = True
            order_in_cache.restaurants[Restaurant.MELANGE]["status"] = "cooked"

        cache.set("orders", internal_order_id, order_in_cache)

        if all_orders_cooked(order_in_cache):
            Order.objects.filter(id=internal_order_id).update(status=OrderStatus.COOKED)
            print("🍳 UPDATED ORDER IN DATABASE TO `COOKED`")
        else:
            # todo: map internal order status to provider's to update database
            pass


@celery_app.task
def bueno_order_processing(internal_order_id: int):
    provider = bueno.Provider()
    cache = CacheService()
    order_in_cache = OrderInCache(
        **cache.get(namespace="orders", key=internal_order_id)
    )

    response: bueno.OrderResponse = provider.create_order(
        bueno.OrderRequestBody(
            order=[
                bueno.OrderItem(**item)
                for item in order_in_cache.restaurants[Restaurant.BUENO]["dishes"]
            ]
        )
    )

    # update cache representation
    order_in_cache.restaurants[Restaurant.BUENO]["external_id"] = response.id
    cache.set(
        namespace="bueno_orders",
        key=response.id,
        instance={"status": response.status, "internal_order_id": internal_order_id},
    )

    print("BUENO ORDER PROCESSED")


@celery_app.task
def delivery_order(internal_order_id: int):
    """Using random provider - start processing delivery orders."""

    cache = CacheService()

    print(f"🚚 DELIVERY PROCESSING STARTED")

    while True:
        order_in_cache = OrderInCache(**cache.get("orders", internal_order_id))

        if all_orders_cooked(order_in_cache):
            break
        else:
            sleep(2)
            print(f"WAITING FOR ORDERS TO BE DELIVERED")

    _delivery_order_task(internal_order_id)

    print(f"🚚 DELIVERED all the orders...")


@celery_app.task
def _delivery_order_task(internal_order_id: int):
    """Using random provider - start processing delivery orders."""

    providers = [uklon.Provider(), uber.Provider()]
    provider = random.choice(providers)
    cache = CacheService()

    addresses: list[str] = []
    comments: list[str] = []

    order_in_cache = OrderInCache(**cache.get("orders", internal_order_id))

    for rest in order_in_cache.restaurants.values():
        addresses.append(rest["address"])
        comments.append(f"ORDER: {rest['external_id']}")

    _response: provider.OrderResponse = provider.create_order(
        provider.OrderRequestBody(addresses=addresses, comments=comments)
    )

    order_in_cache.location = _response.location

    current_status = provider.OrderStatus.NOT_STARTED
    while current_status != provider.OrderStatus.DELIVERED:
        response: provider.OrderResponse = provider.get_order(_response.id)

        print(f"🚙 DELIVERY PROVIDER [{response.status}]: 📍 {response.location}")
        if current_status == response.status:
            sleep(1)
            continue

        current_status = response.status
        order_in_cache.location = response.location

        # update cache
        cache.set("orders", internal_order_id, order_in_cache)

    Order.objects.filter(id=internal_order_id).update(status=current_status)

    # update cache
    for rest in order_in_cache.restaurants.values():
        rest["status"] = provider.OrderStatus.DELIVERED

    cache.set("orders", internal_order_id, order_in_cache)


@celery_app.task
def _schedule_order(order: Order):

    order_in_cache = OrderInCache()

    for item in order.items.all():
        if (restaurant := item.dish.restaurant.name.lower()) == Restaurant.MELANGE:
            order_in_cache.append(restaurant, item)
        elif item.dish.restaurant.name.lower() == Restaurant.BUENO:
            order_in_cache.append(restaurant, item)
        else:
            raise ValueError(
                f"Can not create order for {item.dish.restaurant.name} restaurant"
            )

    cache = CacheService()
    cache.set(namespace="orders", key=order.pk, instance=order_in_cache)

    # start rests and delivery processing
    melange_order_processing.delay(order.pk)
    bueno_order_processing.delay(order.pk)


def schedule_order(order: Order):
    """Add the task to the queue for the future processing."""

    assert type(order.eta) is date

    # todo: remove
    # _schedule_order(order)
    # return None

    # 2025-03-06  -> 2025-03-06-00:00:00 UTC
    if order.eta == date.today():
        print(f"The order will be started processing now")
        return _schedule_order.delay(order)
    else:
        # ETA: 3:00AM will be sent to restaurant APIs
        eta = datetime.combine(order.eta, time(hour=3))
        print(f"The order will be started processing {eta}")
        return _schedule_order.apply_async(args=(order,), eta=eta)
