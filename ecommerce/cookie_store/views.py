import logging
from urllib import parse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
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
from cookie_store.models import Item, Order, Payment, StripePayment


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
                payment = StripePayment()
                payment.charge_id = charge['id']
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


class PaymentRedirect(View):
    def get(self, *args, **kwargs):
        """
        this function is called to submit the payment to pagadito API and
        when the payment gateway returns control to the application
        """
        order_id = kwargs.get('pk', None)
        pg_id = kwargs.get('reference_id', None)
        if order_id and pg_id:
            order = get_object_or_404(Order, pk=order_id)
            try:
                pg_payment = self.check_payment(pg_id, order)
                order.completed = True
                order.payment.charge_id = pg_payment
                order.payment.save()
                order.save()
                messages.info(self.request, "Payment processed successfully")
                return redirect("cookie_store:item-detail")
            except Exception as e:
                logger.error(e.args)
                order.payment.delete()
                return redirect("cookie_store:item-detail")
        else:
            try:
                order = get_object_or_404(Order, completed=False)
                total = order.get_total_price()
                order_xml = self.parse_order(order)
                token, pg_url = self.register_transaction_pg(order.id, total, order_xml)

                payment = Payment()
                payment.amount = order.get_total_price()
                payment.charge_id = token
                payment.save()
                order.payment = payment
                order.save()
                return redirect(pg_url)
            except Exception as e:
                logger.error(e.args)
                return redirect("cookie_store:item-detail")

    def connect_pg(self):
        """
        connects to the pg payment gateway with soap
        :return: token=token to use to register transactions and check status,
        client=the soap client to perform other transactions.
        """
        pg_client = Client(PG_URL)
        resp = pg_client.service.connect(uid=PG_UID, wsk=PG_WSK, format_return="xml")
        result_code = etree.fromstring(resp).find('code').text
        message = etree.fromstring(resp).find('message').text
        if result_code == 'PG1001':
            token = etree.fromstring(resp).find('value').text
            return (token, pg_client)
        else:
            error_string = "There was an error when connecting to the gateway :" + result_code + message
            messages.error(self.request, error_string )
            raise Exception(error_string)


    def register_transaction_pg(self, ern, total, order_xml):
        """
        register the pg transaction with the payment gateway using soap with python zeep client
        :param ern: local order reference number
        :param total: order total
        :param order_xml: the order in xml format
        :return: token = token of registered transaction, url = the url of the payment gateway
        where the user will be redirected
        """
        token, pg_client = self.connect_pg()
        pg_url = pg_client.service.exec_trans(
            token=token,
            ern=ern,
            amount=total,
            details=order_xml,
            currency="USD",
            format_return="xml",
            custom_params="",
            allow_pending_payments=False,
            extended_expiration=True
        )
        result_code = etree.fromstring(pg_url).find('code').text
        message = etree.fromstring(pg_url).find('message').text
        if result_code == 'PG1002':
            url = parse.unquote(etree.fromstring(pg_url).find('value').text)
            parsed_url = parse.urlparse(url)
            charge = parse.parse_qs(parsed_url.query)['token'][0]
            return (charge, url)
        else:
            error_string = "There was an error registering the payment with the gateway :" + result_code + message
            messages.error(self.request, error_string)
            raise Exception(error_string)



    def check_payment(self, pg_id, order):
        """
        checks if the payment was processed by the payment gateway
        :param pg_id: transaction token (is not the same as the payment reference that is returned
        after the payment has been processed)
        :param order: the order that needs to be checked against. the transaction reference is kept
        temporarily in the payment.charge_id. but this field should be use to save the payment reference.
        The field is updated with the payment reference once the payment is confirmed if not, the payment
        object is deleted completely
        :return: True if payment was completed, False otherwise
        """
        if order.payment.charge_id == pg_id:
            token, pg_client = self.connect_pg()
            payment_status = pg_client.service.get_status(
                token=token,
                token_trans=pg_id,
                format_return="xml"
            )
            result = etree.fromstring(payment_status).find('value').find('status').text
            success = isinstance(result, str) and result == 'COMPLETED'
            if success:
                payment_ref = etree.fromstring(payment_status).find('value').find('reference').text
                return payment_ref
            else:
                error_string = "The payment was not completed, status returned by the gateway:" + result
                messages.error(self.request, error_string)
                raise Exception(error_string)
        else:
            raise Http404("Charge token %S doesn't match the current order" % pg_id)




    def parse_order(self, order):
        """
        creates an xml from the order object to use with the soap client
        :param order: the order object
        :return: xml_string of the order
        """
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