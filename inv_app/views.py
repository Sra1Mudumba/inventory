from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, Invoice, Cust_Sale
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
        inv = Cust_Sale.objects.all()
        context = {
            'cust': inv
        }
        html = template.render(context)
        pdf = render_to_pdf('inv.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Inventario_Cust_Sales_%s.pdf" %("12345678")
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
        product_name = request.POST['product_name'].lower()
        product_sr_no = request.POST['product_sr_no']
        quantity = request.POST['quantity']
        price = request.POST['price']
        vendor_name = request.POST['vendor_name']

        prod = Product.objects.filter(product_name = product_name).first()

        if prod is None:
            product = Product(product_name = product_name, product_sr_no = product_sr_no, quantity = quantity, price = price, vendor_name = vendor_name)
            product.save()

        else:
            if prod.price == price:
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
        search = request.POST["search"].lower()

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

    invoice_id = "INV" + uuid.uuid4().hex[:6].upper()
    return render(request, 'invoice.html', {'invoice': invoice_id})

def product_sale(request, invoice_id):
    invoice = Invoice.objects.filter(invoice_id = invoice_id).first()
    CustSaleFormSet = modelformset_factory(Cust_Sale, fields = ('product_name', 'quantity', 'price'))
    form = CustSaleFormSet(queryset = Cust_Sale.objects.filter(invoice_id = invoice_id))

    if request.method == "POST":
        pro_sale = CustSaleFormSet(request.POST)
        if pro_sale.is_valid():
            instances = pro_sale.save(commit = False)

            for instance in instances:
                product_name = instance.product_name.lower()
                quantity = instance.quantity
                price = instance.price

                total_price = quantity * price

                pro = Product.objects.filter(product_name = product_name).first()

                if pro is None:
                    messages.info(request, 'There is no Product named {}'.format(product_name))
                    return redirect('product_sale', invoice_id = invoice.invoice_id)

                if pro.quantity == 0:
                    messages.info(request, 'There is no stock for Product named {}'.format(product_name))
                    return redirect('product_sale', invoice_id = invoice.invoice_id)

                prod_sale = Cust_Sale(product_name = product_name, quantity = quantity, price = price, total_price = total_price, invoice_id = invoice)

                if not pro.quantity < prod_sale.quantity:
                    pro.quantity = pro.quantity - quantity
                    pro.save()
                    prod_sale.save()

                else:
                    messages.error(request, "We don't have the required quantity of {}! We only have {} left!".format(pro.product_name, pro.quantity))

        return redirect('product_sale', invoice_id = invoice.invoice_id)

    return render(request, 'sales.html', {'form': form, 'invoice': invoice})

def confirm(request, invoice_id):
    invoice = Invoice.objects.filter(invoice_id = invoice_id).first()
    product_sale = Cust_Sale.objects.filter(invoice_id = invoice.invoice_id).all()

    total_price = 0
    for prod in product_sale:
        total_price = total_price + prod.price * prod.quantity

    messages.info(request, 'Thank You {}! Visit Again!'.format(invoice.cust_name))

    return render(request, 'confirmation.html', {'total': total_price, 'invoice': invoice.invoice_id, 'product_sale': product_sale})

def delete_entry(request, invoice_id, product_name, quantity):
    invoice = Invoice.objects.filter(invoice_id = invoice_id).first()
    product = Product.objects.filter(product_name = product_name).first()
    product_sale = Cust_Sale.objects.get(Q(invoice_id = invoice_id), Q(product_name = product_name))

    product_sale.delete()
    product.quantity = int(quantity) + product.quantity
    product.save()

    produc_sale = Cust_Sale.objects.filter(invoice_id = invoice_id).all()
    total_price = 0
    for prod in produc_sale:
        total_price = total_price + prod.price * prod.quantity

    return render(request, 'confirmation.html', {'total': total_price, 'invoice': invoice.invoice_id, 'product_sale': produc_sale})


def saledetails(request):
    customer = Cust_Sale.objects.all().order_by('-sale_date')
    return render(request, 'salesdetails.html', {'cust': customer})

class GenerateBill(View):
    def get(self, request, *args, **kwargs):
        template = get_template('billing.html')
        inv_id = self.kwargs['invoice_id']
        inv = Cust_Sale.objects.filter(invoice_id = inv_id)
        invo = Cust_Sale.objects.filter(invoice_id = inv_id).first()
        total_price = 0

        for i in inv:
            total_price = total_price + i.total_price
        
        context = {
            'cust': inv,
            'invo':invo,
            'tot': total_price,
        }
        
        html = template.render(context)
        pdf = render_to_pdf('billing.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Inventario_Cust_Sales_%s.pdf" %("12345678")
            content = "inline; filename='%s'" %(filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" %(filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
