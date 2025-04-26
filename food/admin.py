from django.contrib import admin
from django.http.response import HttpResponseRedirect
from .models import Dish, DishOrderItem, Order, Restaurant

admin.site.register(Restaurant)


def import_csv(self, request, queryset):
    print("testing import CSV custom action")
    return HttpResponseRedirect("/import-dishes")


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "restaurant")
    search_fields = ("name",)
    list_filter = ("name", "restaurant")
    actions = ["import_csv"]


class DishOrderItemInline(admin.TabularInline):
    model = DishOrderItem


@admin.register(Order)
class DishesOrderAdmin(admin.ModelAdmin):
    list_display = ("__str__", "id", "status")
    inlines = (DishOrderItemInline,)


admin.site.add_action(import_csv)
