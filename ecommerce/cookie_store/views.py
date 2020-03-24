from django.shortcuts import render

# Create your views here.
from cookie_store.models import Item


def item_detail(request):
    #just use one product
    context = {
        'item': Item.objects.first()
    }
    return render(request, 'product-page.html', context)