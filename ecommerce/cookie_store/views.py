from django.shortcuts import render

# Create your views here.
from cookie_store.models import Item


def item_list(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, 'product-page.html', context)