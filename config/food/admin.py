from django.contrib import admin
from .models import Restaurant, Dish, DishesOrder, DishOrderItem

admin.site.register(Restaurant)
admin.site.register(Dish)
admin.site.register(DishesOrder)
admin.site.register(DishOrderItem)