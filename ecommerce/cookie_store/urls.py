from django.urls import path

from cookie_store.views import item_detail, add_to_cart

app_name = 'cookie_store'

urlpatterns = [
    path('', item_detail, name='item-detail'),
    path('add-to-cart/<pk>', add_to_cart, name='add-to-cart'),
]
