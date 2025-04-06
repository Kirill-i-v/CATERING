from django.core.handlers.wsgi import WSGIRequest
from rest_framework import status, viewsets, routers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Dish, DishOrderItem, Order, Restaurant
from .serializers import DishSerializer, OrderCreateSerializer, RestaurantSerializer
from .enums import OrderStatus
from shared.cache import CacheService


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

        order = Order.objects.create(
            status=OrderStatus.NOT_STARTED,
            user=request.user,
            eta=serializer.validated_data["eta"],
        )
        print(f"New Food Order is created: {order.pk}.\nETA: {order.eta}")

        cache = CacheService()
        cache_key = f"orders:{OrderStatus.NOT_STARTED}"
        existing = cache.get("orders", OrderStatus.NOT_STARTED) or []
        existing.append(order.pk)
        cache.set("orders", OrderStatus.NOT_STARTED, existing)

        try:
            dishes_order = serializer.validated_data["food"]
        except KeyError:
            raise ValueError("Food order is not properly built")

        for dish_order in dishes_order:
            instance = DishOrderItem.objects.create(
                dish=dish_order["dish"], quantity=dish_order["quantity"], order=order
            )
            print(f"New Dish Order Item is created: {instance.pk}")

        return Response(data={
                "id": order.pk,
                "status": order.status,
                "eta": order.eta,
                "total": 9999,
            },
            status=status.HTTP_201_CREATED,
        )

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
