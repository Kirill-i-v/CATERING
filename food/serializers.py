from rest_framework import serializers
from .models import Dish, Restaurant, Order, DishOrderItem


class DishOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishOrderItem
        fields = ['dish', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'eta', 'items']

    def get_items(self, obj):
        items = DishOrderItem.objects.filter(order=obj)
        return DishOrderItemSerializer(items, many=True).data


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"


class DishSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer()

    class Meta:
        model = Dish
        fields = "__all__"


class DishOrderSerializer(serializers.Serializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dish.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class OrderCreateSerializer(serializers.Serializer):
    food = DishOrderSerializer(many=True)
    eta = serializers.DateField()
    total = serializers.IntegerField(min_value=1, read_only=True)
