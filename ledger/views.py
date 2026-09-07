from django.shortcuts import (
    render,
    redirect
)

from core.models import (
    Customer,
    Payment
)


def party_ledger(request, customer_id):

    customer = Customer.objects.get(
        id=customer_id
    )

    transactions = []

    for invoice in customer.invoice_set.all():

        transactions.append({
            "date": invoice.invoice_date,
            "particular": invoice.invoice_number,
            "debit": invoice.net_amount,
            "credit": 0
        })

    for payment in customer.payments.all():

        transactions.append({
            "date": payment.payment_date,
            "particular": f"Receipt {payment.reference_no}",
            "debit": 0,
            "credit": payment.amount
        })

    transactions.sort(
        key=lambda x: x["date"]
    )

    balance = 0

    for txn in transactions:

        balance += txn["debit"]

        balance -= txn["credit"]

        txn["balance"] = balance

    returns = SalesReturn.objects.filter(
    invoice__customer=customer
    )

    for sales_return in returns:

        transactions.append({

            "date": sales_return.return_date,

            "particular":
                f"Sales Return {sales_return.id}",

            "debit": 0,

            "credit":
                sales_return.credit_amount
        })


    return render(
        request,
        'ledger/party_ledger.html',
        {
           {
                'customer': customer,
                'transactions': transactions
            }
        }
    )

def payment_create(request):

    customers = Customer.objects.all()

    if request.method == "POST":

        customer = Customer.objects.get(
            id=request.POST.get("customer")
        )

        payment = Payment.objects.create(
            customer=customer,
            payment_date=request.POST.get(
                "payment_date"
            ),
            amount=request.POST.get(
                "amount"
            ),
            reference_no=request.POST.get(
                "reference_no"
            ),
            remarks=request.POST.get(
                "remarks"
            )
        )

        return redirect(
            'party_ledger',
            customer_id=customer.id
        )

    return render(
        request,
        'ledger/payment_create.html',
        {
            'customers': customers
        }
    )