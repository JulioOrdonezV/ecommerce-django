from django.urls import path

from cookie_store.views import item_detail, add_to_cart, OrderSummaryView

app_name = 'cookie_store'

urlpatterns = [
    path('', item_detail, name='item-detail'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-sumary'),
    path('add-to-cart/<pk>', add_to_cart, name='add-to-cart'),
]
