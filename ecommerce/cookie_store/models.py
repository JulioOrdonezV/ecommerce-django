from django.db import models

# Create your models here.
from django.urls import reverse


class Item(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.FloatField()

    def __str__(self):
        return self.nombre
    def get_add_to_cart_url(self):
        return reverse('cookie_store:add-to-cart', kwargs={
            'pk': self.id
        })


class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)


class Order(models.Model):
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_orden = models.DateTimeField()
    completada = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
