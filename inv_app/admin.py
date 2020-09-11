from django.contrib import admin
from .models import Product, Invoice, Cust_Sale

# Register your models here.
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(Cust_Sale)