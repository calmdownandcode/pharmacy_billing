from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_create, name='invoice_create'),

    path(
        'invoice/<int:invoice_id>/',
        views.invoice_detail,
        name='invoice_detail'
    ),

    path(
    'invoice/<int:invoice_id>/print/',
    views.print_invoice,
    name='print_invoice'
    ),
]