from django.contrib import admin

from .models import Item, PriceItem

admin.site.register(Item)
admin.site.register(PriceItem)
