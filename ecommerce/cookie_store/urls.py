from django.urls import path

from cookie_store.views import (
    item_detail,
    add_to_cart,
    OrderSummaryView,
    checkoutView,
    PaymentView,
    PaymentRedirect
)

app_name = 'cookie_store'

urlpatterns = [
    path('', item_detail, name='item-detail'),
    path('checkout', checkoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-sumary'),
    path('add-to-cart/<pk>', add_to_cart, name='add-to-cart'),
    path('payment/<payment_option>', PaymentView.as_view(), name='payment'),
    path('payment-redirect', PaymentRedirect.as_view(), name="payment-redirect"),
    path('payment-redirect/<pk>/<reference_id>', PaymentRedirect.as_view(), name="payment-return")
]
