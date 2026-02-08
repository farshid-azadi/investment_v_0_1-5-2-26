from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.wallet.models import WithdrawalRequest, Transaction

@transaction.atomic
def request_withdrawal(user, amount, wallet_address):
    wallet = user.wallet

    if wallet.balance < amount:
        raise ValidationError("Insufficient balance")

    wallet.balance -= amount
    wallet.locked_balance += amount
    wallet.save(update_fields=["balance", "locked_balance"])

    WithdrawalRequest.objects.create(
        user=user,
        amount=amount,
        wallet_address=wallet_address
    )

    Transaction.objects.create(
        user=user,
        amount=-amount,
        transaction_type="withdraw",
        reference="Withdrawal request"
    )
