from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.quantity})"


class PriceItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} @ {self.unit_price}"
