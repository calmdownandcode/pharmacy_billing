from django.shortcuts import render
from core.models import Batch


def stock_report(request):

    batches = Batch.objects.select_related(
        'product'
    ).all().order_by(
        'product__name'
    )

    return render(
        request,
        'reports/stock_report.html',
        {
            'batches': batches
        }
    )
