from django.urls import path
from . import views

urlpatterns = [

    path(
        'party/<int:customer_id>/',
        views.party_ledger,
        name='party_ledger'
    ),

    path(
    'payment/new/',
    views.payment_create,
    name='payment_create'
    ),

]