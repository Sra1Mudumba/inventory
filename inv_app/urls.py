from django.urls import path, include
from . import views
from .views import GeneratePDF, GenerateBill

urlpatterns = [
    path('', views.index, name = "index"),
    path('inventory/', views.inventory, name = "inventory"),
    path('sales/', views.invoice, name = "invoice"),
    path('sales/<invoice_id>/', views.product_sale, name = "product_sale"),
    path('sales/<invoice_id>/confirmation', views.confirm, name = "confirm"),
    path('saledetails/', views.saledetails, name = "saledetails"),
    path('sales_details/', GeneratePDF.as_view()),
    path('bill/<invoice_id>', GenerateBill.as_view()),
]
