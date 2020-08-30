from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from random import randint
from django.utils.crypto import get_random_string

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=100)
    product_sr_no = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.FloatField(max_length = 10)
    vendor_name = models.CharField(max_length=100)

    def __str__(self):
        return self.product_name

class Invoice(models.Model):
    invoice_id = models.CharField(primary_key=True, max_length = 10)
    cust_name = models.CharField(max_length = 100)
    cust_phone = PhoneNumberField()

class CustomerSale(models.Model):
    product_name = models.CharField(max_length = 100)
    product_sr_no = models.CharField(max_length = 100)
    quantity = models.IntegerField()
    price = models.FloatField(max_length = 10)
    total_price = models.FloatField(max_length = 10)
    invoice_id = models.ForeignKey(Invoice, on_delete = models.CASCADE)
    delete_product = models.BooleanField()
    sale_date = models.DateTimeField(auto_now_add = True)

