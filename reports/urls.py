from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock_report, name='stock_report'),
    path(
    'outstanding/',
    views.outstanding_report,
    name='outstanding_report'
    ),
    path(
    'expiry/',
    views.expiry_report,
    name='expiry_report'
    ),
    path(
    'low-stock/',
    views.low_stock_report,
    name='low_stock_report'
    ),
]