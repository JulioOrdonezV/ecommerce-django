from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.utils import timezone

from cookie_store.models import Item, OrderItem, Order


def item_detail(request):
    #just use one product
    context = {
        'item': Item.objects.first()
    }
    return render(request, 'product-page.html', context)

def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_item = OrderItem.objects.filter(order__completada=False).get_or_create(
        item=item
    )[0]
    order_qs = Order.objects.filter(completada=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__id=item.id).exists():
            order_item.cantidad += 1
            order_item.save()
        else:
            order.items.add(order_item)
    else:
        order_date = timezone.now()
        order = Order.objects.create(fecha_orden=order_date)
        order.items.add(order_item)

    return redirect("cookie_store:item-detail")