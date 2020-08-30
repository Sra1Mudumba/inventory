from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, Invoice, CustomerSale
from django.forms import modelformset_factory
import uuid
from django import template
from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import get_template
from .utils import render_to_pdf 

class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        template = get_template('inv.html')
        inv = CustomerSale.objects.all()
        context = {
            'cust': inv
        }
        html = template.render(context)
        pdf = render_to_pdf('inv.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Inventario_Sales_%s.pdf" %("12341231")
            content = "inline; filename='%s'" %(filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" %(filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")

register = template.Library()

@register.filter()
def rangeof(m):
    return range(m)

context = {}


# Create your views here.
def index(request):
    if request.method == "POST":
        product_name = request.POST['product_name']
        product_sr_no = request.POST['product_sr_no']
        quantity = request.POST['quantity']
        price = request.POST['price']
        vendor_name = request.POST['vendor_name']

        prod = Product.objects.filter(product_name = product_name).first()

        if prod is None:
            product = Product(product_name = product_name, product_sr_no = product_sr_no, quantity = quantity, price = price, vendor_name = vendor_name)
            product.save()

        else:
            if prod.vendor_name == vendor_name:
                product = Product.objects.filter(product_name = product_name).first()
                product.quantity = product.quantity + int(quantity)
                product.save()

            else:
                product = Product(product_name = product_name, product_sr_no = product_sr_no, quantity = quantity, price = price, vendor_name = vendor_name)
                product.save()

        messages.success(request, 'Product Details are added!', extra_tags = "success")
        messages.info(request, 'You can add some more products!', extra_tags = "info")
        return redirect('index')

    return render(request, 'index.html')

def inventory(request):
    if 'term' in request.POST:
        qs = Product.objects.filter(product_name_istartswith = request.POST.get('term'))
        titles = list()
        for pro in qs:
            titles.append(pro.product_name)

        return JsonResponse(titles, safe=False)

    if request.method == "POST":
        search = request.POST["search"]

        prod = Product.objects.filter(product_name = search).all()

        if prod is None:
            messages.info(request, 'Product not found')
            return redirect('inventory')

        else:
            return render(request, 'inventory-2.html', {'searches': prod})

    products = Product.objects.all()
    return render(request, 'inventory.html', {'products': products})

def invoice(request):
    if request.method == "POST":
        invoice_id = request.POST["invoice"]
        cust_name = request.POST["cust_name"]
        cust_tel = request.POST["cust_tel"]
        cust_phone = request.POST["cust_phone"]

        cust_ph = cust_tel + cust_phone
        invoice = Invoice(invoice_id = invoice_id, cust_name = cust_name, cust_phone = cust_ph)
        invoice.save()
        return redirect('product_sale', invoice_id = invoice.invoice_id)

    invoice_id = "SOO" + uuid.uuid4().hex[:6].upper()
    return render(request, 'invoice.html', {'invoice': invoice_id})

def product_sale(request, invoice_id):
    invoice = Invoice.objects.filter(invoice_id = invoice_id).first()
    CustomerSaleFormSet = modelformset_factory(CustomerSale, fields = ('product_name', 'product_sr_no', 'quantity', 'price', 'delete_product'), extra = 5)
    form = CustomerSaleFormSet(queryset = CustomerSale.objects.filter(invoice_id = invoice_id))

    if request.method == "POST":
        pro_sale = CustomerSaleFormSet(request.POST)
        if pro_sale.is_valid():
            instances = pro_sale.save(commit = False)

            for instance in instances:
                product_name = instance.product_name
                product_sr_no = instance.product_sr_no
                quantity = instance.quantity
                price = instance.price
                delete_pro = instance.delete_product

                total_price = quantity * price

                pro = Product.objects.filter(product_sr_no = product_sr_no).first()
                prod_sale = CustomerSale(product_name = product_name, product_sr_no = product_sr_no, quantity = quantity, price = price, total_price = total_price, invoice_id = invoice)

                if not delete_pro:
                    if not pro.quantity < prod_sale.quantity:
                        pro.quantity = pro.quantity - quantity
                        pro.save()
                        prod_sale.save()

                    else:
                        messages.error(request, "We don't have the required quantity! We only have {} left!".format(pro.quantity))

                else:
                    prod = CustomerSale.objects.filter(product_sr_no = product_sr_no)
                    prod.delete()

        return redirect('product_sale', invoice_id = invoice.invoice_id)

    return render(request, 'sales.html', {'form': form, 'invoice': invoice})

def confirm(request, invoice_id):
    invoice = Invoice.objects.filter(invoice_id = invoice_id).first()
    product_sale = CustomerSale.objects.filter(invoice_id = invoice.invoice_id).all()

    total_price = 0
    for prod in product_sale:
        total_price = total_price + prod.price * prod.quantity

    messages.info(request, 'Thank You {}! Visit Again!'.format(invoice.cust_name))

    return render(request, 'confirmation.html', {'total': total_price, 'invoice': invoice.invoice_id})

def times():
    inv = Invoice.objects.all().count()
    return inv

def saledetails(request):
    customer = CustomerSale.objects.all().order_by('-sale_date')
    return render(request, 'salesdetails.html', {'cust': customer})