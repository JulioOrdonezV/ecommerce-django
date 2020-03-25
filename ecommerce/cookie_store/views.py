from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.utils import timezone

from cookie_store.models import Item, Order


def item_detail(request):
    #just use one product
    context = {
        'item': Item.objects.first()
    }
    return render(request, 'product-page.html', context)

def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order, created = Order.objects.filter(completada=False).get_or_create(
        items=item
    )
    if created:
        messages.info(request, "Galleta agregada al carrito")
    else:
        order.cantidad += 1
        order.save()
        messages.info(request, "Cantidad de galletas actualizada")
    return redirect("cookie_store:item-detail")