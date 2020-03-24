from django.shortcuts import render

# Create your views here.
from cookie_store.models import Item


def itemDetailView(request):
    #just use one product
    context = {
        'items': Item.objects.first()
    }
    return render(request, 'product-page.html', context)