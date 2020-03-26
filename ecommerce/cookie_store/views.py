from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View

from cookie_store.forms import CheckoutForm, CreditCardForm
from cookie_store.models import Item, Order


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(completada=False)
            return render(self.request,"order_summary.html", context={'order': order} )
        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have an order")
            return redirect("/")


class checkoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form
        }
        return render(self.request, 'checkout-page.html', context)
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        if form.is_valid():
            payment_option = form.cleaned_data.get('payment_options')
            messages.warning(self.request, "Order placed")
            return redirect('cookie_store:item-detail')
        messages.warning(self.request, "Something didn't work")
        return redirect('cookie_store:item-detail')


class PaymentView(View):
    def get(self, *args, **kwargs):
        form = CreditCardForm()
        context = {
            'form': form
        }
        return render(self.request, "payment.html", context)
    def post(self, *args, **kwargs):
        form = CreditCardForm(self.request.POST or None)
        if form.is_valid():
            pass
        return redirect('coookie_store:item-detail')


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