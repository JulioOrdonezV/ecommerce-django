from django.db import models

# Create your models here.
class Item(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.FloatField()

    def __str__(self):
        return self.nombre

class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)

class Order(models.Model):
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField()
    completada = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
