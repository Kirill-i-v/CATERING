import enum
from dataclasses import asdict, dataclass
from config.settings import UBER_BASE_URL
import httpx


class OrderStatus(enum.StrEnum):
    NOT_STARTED = "not started"
    DELIVERY = "delivery"
    DELIVERED = "delivered"


@dataclass
class OrderRequestBody:
    # = field(default_factory=list)
    addresses: list[str]
    comments: list[str]


@dataclass
class OrderResponse:
    id: str
    status: OrderStatus
    location: tuple[float, float]
    addresses: list[str]
    comments: list[str]


class Provider:
    BASE_URL = UBER_BASE_URL

    @classmethod
    def create_order(cls, order: OrderRequestBody):
        response: httpx.Response = httpx.post(cls.BASE_URL, json=asdict(order))
        response.raise_for_status()

        return OrderResponse(**response.json())

    @classmethod
    def get_order(cls, order_id: str):
        response: httpx.Response = httpx.get(f"{cls.BASE_URL}/{order_id}")
        response.raise_for_status()

        return OrderResponse(**response.json())
