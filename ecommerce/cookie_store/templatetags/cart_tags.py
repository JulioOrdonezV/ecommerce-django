from django import template
from cookie_store.models import Order

register = template.Library()

@register.simple_tag()
def cart_item_count():
    order_qs = Order.objects.filter(completada=False)
    if order_qs.exists():
        return order_qs[0].cantidad
    return 0
