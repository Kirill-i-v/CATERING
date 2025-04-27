from celery.result import AsyncResult
from django.core.handlers.wsgi import WSGIRequest
from rest_framework import routers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .enums import OrderStatus
from .models import Dish, DishOrderItem, Order, Restaurant
from .serializers import DishSerializer, OrderCreateSerializer, RestaurantSerializer
from .services import schedule_order, all_orders_cooked, delivery_order
from shared.cache import CacheService
from django.db import transaction
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework import status
from food.models import Order
from food.serializers import OrderSerializer


class OrderRetrieveView(APIView):
    def get(self, request, order_id):
        cache = CacheService()
        order_in_cache = cache.get("orders", order_id)

        if order_in_cache:
            return Response(order_in_cache, status=status.HTTP_200_OK)

        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
def bueno_webhook(request):
    data: dict = json.loads(json.dumps(request.POST))

    cache = CacheService()
    _order: dict = cache.get("bueno_orders", data["id"])

    order: Order = Order.objects.get(id=_order["internal_order_id"])

    Order.update_from_provider_status(id_=order.id, status=data["status"], delivery=False)

    order_in_cache = cache.get("orders", order.id)
    if all_orders_cooked(order_in_cache):
        # Schedule the delivery if all orders are cooked
        delivery_order.delay(order.id)

    return JsonResponse({"message": "ok"})


class FoodAPIViewSet(viewsets.GenericViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    cache = CacheService()

    # HTTP GET /food/dishes
    @action(methods=["get"], detail=False)
    def dishes(self, request):
        dishes = Dish.objects.all()
        serializer = DishSerializer(dishes, many=True)
        return Response(data=serializer.data)

    # HTTP POST /food/orders
    @action(methods=["post"], detail=False)
    def orders(self, request: WSGIRequest):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not isinstance(serializer.validated_data, dict):
            raise ValueError("Invalid order format")

        order: Order = Order.objects.create(
            status=OrderStatus.NOT_STARTED,
            user=request.user,
            eta=serializer.validated_data["eta"],
        )

        try:
            dishes_order = serializer.validated_data["food"]
        except KeyError:
            raise ValueError("Food order is not properly built")

        for dish_order in dishes_order:
            instance = DishOrderItem.objects.create(
                dish=dish_order["dish"], quantity=dish_order["quantity"], order=order
            )
            print(f"New Dish Order Item is created: {instance.pk}")

        schedule_order(order=order)
        print(f"New Food Order is created: {order.pk}.\nETA: {order.eta}")

        return Response(data={
                "id": order.pk,
                "status": order.status,
                "eta": order.eta,
                "total": 9999,
            },
            status=status.HTTP_201_CREATED,
        )

        # HTTP POST /food/orders/<ID>
    @action(methods=["get"], detail=False, url_path=r"orders/(?P<id>\d+)")
    def order_retrieve(self, request: WSGIRequest, id: int):
        order: Order = Order.objects.get(id=id)
        cache = CacheService()

        order_in_cache = cache.get("orders", order.pk)

        return Response(data=order_in_cache)

    # HTTP GET /food/restaurants
    @action(methods=["get"], detail=False)
    def list_restaurants(self, request):
        restaurants = self.get_queryset()
        serializer = self.get_serializer(restaurants, many=True)
        return Response(data=serializer.data)

    # HTTP POST /food/restaurants
    @action(methods=["post"], detail=False)
    def create_restaurant(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # HTTP GET /food/restaurants/{ID}
    @action(methods=["get"], detail=True)
    def retrieve_restaurant(self, request, pk=None):
        try:
            restaurant = self.get_queryset().get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(restaurant)
        return Response(data=serializer.data)


router = routers.DefaultRouter()
router.register(
    prefix="food",
    viewset=FoodAPIViewSet,
    basename="food",
)
