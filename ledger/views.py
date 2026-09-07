from django.shortcuts import render, redirect, get_object_or_404
from core.models import Customer, Payment, SalesReturn
from datetime import date

def party_ledger(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    transactions = []

    # 1. Gather all invoices (Debits)
    for invoice in customer.invoice_set.all():
        transactions.append({
            "date": invoice.invoice_date,
            "particular": invoice.invoice_number,
            "debit": float(invoice.net_amount),
            "credit": 0.0
        })

    # 2. Gather all direct payments (Credits)
    for payment in customer.payments.all():
        transactions.append({
            "date": payment.payment_date,
            "particular": f"Receipt {payment.reference_no or payment.id}",
            "debit": 0.0,
            "credit": float(payment.amount)
        })

    # 3. Gather all Sales Returns (Credits) - Fixed placement optimization
    returns = SalesReturn.objects.filter(invoice__customer=customer)
    for sales_return in returns:
        transactions.append({
            "date": sales_return.return_date,
            "particular": f"Sales Return #{sales_return.id}",
            "debit": 0.0,
            "credit": float(sales_return.credit_amount)
        })

    # 4. Sort everything globally by transaction date
    transactions.sort(key=lambda x: x["date"])

    # 5. Compute chronological incremental balance running metrics
    balance = 0.0
    for txn in transactions:
        balance += txn["debit"]
        balance -= txn["credit"]
        txn["balance"] = balance

    return render(
        request,
        'ledger/party_ledger.html',
        {
            'customer': customer,
            'transactions': transactions
        }
    )

def payment_create(request):
    customers = Customer.objects.all()

    if request.method == "POST":
        customer = get_object_or_404(Customer, id=request.POST.get("customer"))
        Payment.objects.create(
            customer=customer,
            payment_date=request.POST.get("payment_date"),
            amount=request.POST.get("amount"),
            reference_no=request.POST.get("reference_no"),
            remarks=request.POST.get("remarks")
        )
        return redirect('party_ledger', customer_id=customer.id)

    return render(
        request,
        'ledger/payment_create.html',
        {'customers': customers}
    )
