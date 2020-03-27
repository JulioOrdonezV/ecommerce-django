from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.base import View

import stripe

from ecommerce.settings import STRIPE_API_KEY, STRIPE_PUBLIC_KEY

stripe.api_key = STRIPE_API_KEY

from cookie_store.forms import CheckoutForm, CreditCardForm
from cookie_store.models import Item, Order, Payment


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
            if payment_option == 'S':
                return redirect("cookie_store:payment", payment_option='stripe')
            elif payment_option == 'P':
                return redirect("cookie_store:payment", payment_option='pagadito')
            else:
                messages.warning(self.request, "Invalid payment option selected")
                return redirect('cookie_store:checkout')
        messages.warning(self.request, form.errors)
        return redirect('cookie_store:order-sumary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        form = CreditCardForm()
        context = {
            'form': form,
            'payment': kwargs.get('payment_option')
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        form = CreditCardForm(self.request.POST or None)
        if form.is_valid():
            expiry = form.cleaned_data.get('cc_expiry')
            cvc = form.cleaned_data.get('cc_code')
            number = form.cleaned_data.get('cc_number')
            try:
                token = stripe.Token.create(
                    card={
                        'number': number,
                        'exp_month': expiry.month,
                        'exp_year': expiry.year,
                        'cvc': cvc
                    },
                    api_key=STRIPE_PUBLIC_KEY
                )
                order = Order.objects.get(completada=False)
                total = int(order.get_total_price() * 100)  # cents
                charge = stripe.Charge.create(
                    amount=total,
                    currency='usd',
                    description='Example charge',
                    source=token,
                )

                order.completada = True
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.credit_card = "*" * (len(number) - 4) + number[-4:]
                payment.amount = order.get_total_price()
                payment.save()
                order.payment = payment
                order.save()

            except stripe.error.CardError as e:
                #TODO enable logging
                # Since it's a decline, stripe.error.CardError will be caught
                #print('Status is: %s' % e.http_status)
                #e.error.type, e.error.code
                body = e.json_body
                err = body.get('error',{})
                messages.error(self.request,f"{err.get('message')}")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.RateLimitError as e:
                messages.warning(self.request,"Too many requests made to the API too quickly")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.InvalidRequestError as e:
                messages.warning(self.request,"Invalid parameters were supplied to Stripe's API")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.AuthenticationError as e:
                messages.warning(self.request, "Authentication with Stripe's API failed")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.APIConnectionError as e:
                messages.warning(self.request,"Network communication with Stripe failed")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.StripeError as e:
                messages.warning(self.request, "Something went wrong, you haven't been charged. Try again")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except Exception as e:
                # TODO enable logging
                messages.warning(self.request, "Something unexpected happened!")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            messages.success(self.request, "Payment processed successfully")
            return redirect("cookie_store:item-detail")
        else:
            messages.warning(self.request, form.errors)
            return redirect(reverse("cookie_store:payment", kwargs={
                'payment_option': kwargs.get('payment_option')}))

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
        messages.info(request, "Cookie added to the shopping cart")

    else:
        order.cantidad += 1
        order.save()
        messages.info(request, "Cookie quantity updated")
    return redirect("cookie_store:item-detail")