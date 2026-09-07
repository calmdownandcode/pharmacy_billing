from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.purchase_create, name='purchase_create'),
    path(
        '<int:purchase_id>/',
         views.purchase_detail,
         name='purchase_detail'
    ),
    path(
    'return/<int:purchase_id>/',
    views.create_purchase_return,
    name='create_purchase_return'
    ),
]