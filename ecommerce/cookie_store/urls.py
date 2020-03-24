from django.contrib import admin
from django.urls import path, include

from cookie_store.views import item_list

app_name = 'cookie_store'

urlpatterns = [
    path('', item_list, name='item-list'),
]
