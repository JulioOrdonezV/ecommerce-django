import logging
from urllib import parse

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from lxml import etree, objectify
from zeep import Client
from django.views.generic.base import View

import stripe
from ecommerce.settings import PG_UID,PG_WSK, PG_URL
from ecommerce.settings import STRIPE_API_KEY, STRIPE_PUBLIC_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_API_KEY

from cookie_store.forms import CheckoutForm, CreditCardForm
from cookie_store.models import Item, Order, Payment


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(completed=False)
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
                return redirect("cookie_store:payment-redirect")
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
                order = Order.objects.get(completed=False)
                total = int(order.get_total_price() * 100)
                token = stripe.Token.create(
                    card={
                        'number': number,
                        'exp_month': expiry.month,
                        'exp_year': expiry.year,
                        'cvc': cvc
                    },
                    api_key=STRIPE_PUBLIC_KEY
                )
                  # cents
                charge = stripe.Charge.create(
                    amount=total,
                    currency='usd',
                    description=str(order),
                    source=token,
                )

                order.completed = True
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.credit_card = "*" * (len(number) - 4) + number[-4:]
                payment.cvc = "*" * len(cvc)
                payment.expire = expiry
                payment.amount = order.get_total_price()
                payment.save()
                order.payment = payment
                order.save()

            except stripe.error.CardError as e:

                # Since it's a decline, stripe.error.CardError will be caught
                #print('Status is: %s' % e.http_status)
                #e.error.type, e.error.code
                body = e.json_body
                err = body.get('error',{})
                messages.info(self.request,f"{err.get('message')}")
                logger.info(f"{err.get('message')}")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.RateLimitError as e:
                messages.warning(self.request,"Too many requests made to the API too quickly")
                logger.warning("Too many requests made to the API too quickly")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.InvalidRequestError as e:
                messages.warning(self.request,"Invalid parameters were supplied to Stripe's API")
                logger.info("Invalid parameters were supplied to Stripe's API")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.AuthenticationError as e:
                messages.warning(self.request, "Authentication with Stripe's API failed")
                logger.info("Authentication with Stripe's API failed")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.APIConnectionError as e:
                messages.warning(self.request,"Network communication with Stripe failed")
                logger.warning("Network communication with Stripe failed")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except stripe.error.StripeError as e:
                messages.warning(self.request, "Something went wrong, you haven't been charged. Try again")
                body = e.json_body
                err = body.get('error', {})
                logger.error(err.get('message') + " general Stripe error")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            except Exception as e:
                logger.error(f"{e}" + " application error")
                messages.warning(self.request, "Something unexpected happened!")
                return redirect("cookie_store:payment", payment_option=kwargs.get('payment_option'))
            messages.success(self.request, "Payment processed successfully")
            return redirect("cookie_store:item-detail")
        else:
            for field in form:
                if field.errors:
                    field.field.widget.attrs['class'] = 'form-control is-invalid'
            logger.warning("No information was sent to Stripe due to form validation errors")
            return render(self.request, "payment.html", {'form': form})

        return redirect('coookie_store:item-detail')

class PaymentRedirect(View):
    def get(self, *args, **kwargs):
        """this function is called to submit the payment to pagadito API and it
        also handles the response from the payment gateway"""
        order_id = kwargs.get('pk', None)
        pg_id = kwargs.get('reference_id', None)
        if order_id and pg_id:
            order = get_object_or_404(Order, pk=order_id)
            payment = self.check_payment(pg_id)
            if payment:
                order.completed=True
                order.save()
                messages.info("Payment processed successfully")
                return redirect("cookie_store:item-detail")
        else:
            try:
                order = Order.objects.get(completed=False)
                total = order.get_total_price()
                order_xml = self.parse_order(order)
                pg_client = Client(PG_URL)
                resp = pg_client.service.connect(uid=PG_UID, wsk=PG_WSK, format_return="xml")
                token = etree.fromstring(resp).find('value').text

                pg_url = pg_client.service.exec_trans(
                    token=token,
                    ern=order.id,
                    amount=total,
                    details=order_xml,
                    currency="USD",
                    format_return="xml",
                    custom_params="",
                    allow_pending_payments=False,
                    extended_expiration=True
                )
                url = parse.unquote(etree.fromstring(pg_url).find('value').text)
                return redirect(url)
            except Exception as e:
                messages.warning(self.request, "Something unexpected happened!")
                return redirect("cookie_store:item-detail")

    def check_payment(self, pg_id):
        pg_client = Client(PG_URL)
        resp = pg_client.service.connect(uid=PG_UID, wsk=PG_WSK, format_return="xml")
        token = etree.fromstring(resp).find('value').text
        payment_status = pg_client.service.get_status(
            token=token,
            token_trans=pg_id,
            format_return="xml"
        )
        result = etree.fromstring(payment_status).find('status').text
        return result == 'COMPLETED'


    def parse_order(self, order):
        xml_root='''<?xml version="1.0"?><detail></detail>'''
        xml_obj = objectify.fromstring(xml_root)
        xml_obj.quantity = order.quantity
        xml_obj.description = order.items.name
        xml_obj.price = order.items.price
        xml_obj.product_url = reverse("cookie_store:item-detail")
        objectify.deannotate(xml_obj)
        etree.cleanup_namespaces(xml_obj)
        xml_string = etree.tostring(xml_obj)
        return xml_string


def item_detail(request):
    #just use one product
    context = {
        'item': Item.objects.first()
    }
    return render(request, 'product-page.html', context)

def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order, created = Order.objects.filter(completed=False).get_or_create(
        items=item
    )
    if created:
        messages.info(request, "Cookie added to the shopping cart")

    else:
        order.quantity += 1
        order.save()
        messages.info(request, "Cookie quantity updated")
    return redirect("cookie_store:item-detail")