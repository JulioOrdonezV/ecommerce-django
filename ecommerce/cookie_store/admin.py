from django.contrib import admin
from .models import Order, Item
# Register your models here.

admin.site.register(Item)
admin.site.register(Order)