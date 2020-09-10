from django.contrib import admin
from .models import Product, Invoice, CustomerSale

# Register your models here.
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(CustomerSale)