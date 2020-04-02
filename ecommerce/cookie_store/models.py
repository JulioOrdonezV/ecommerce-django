from django.db import models
from polymorphic.models import PolymorphicModel
# Create your models here.
from django.urls import reverse


class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()


    def __str__(self):
        return self.name
    def get_add_to_cart_url(self):
        return reverse('cookie_store:add-to-cart', kwargs={
            'pk': self.id
        })


class Order(models.Model):
    order_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)
    items = models.ForeignKey("Item", on_delete=models.CASCADE)
    payment = models.ForeignKey("Payment", on_delete=models.SET_NULL,
                                blank=True, null=True)
    def get_total_price(self):
        return self.items.price * self.quantity


    def __str__(self):
        if not self.id: #si el objeto no ha sido guardado o es nuevo
            return ""
        return f"{self.id}" + " " + f"{self.quantity}" \
               + " of " + f"{self.items.name}" + " total= " + f"{self.get_total_price()}"

class Payment(PolymorphicModel):
    charge_id = models.CharField(max_length=50)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class StripePayment(Payment):
    credit_card= models.CharField(max_length=20)
    cvc = models.CharField(max_length=4)
    expire = models.DateField()