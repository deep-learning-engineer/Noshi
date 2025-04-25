from django.db import models

from bank_accounts.models import BankAccount


class TransactionType(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    transaction_id = models.AutoField(primary_key=True)
    type = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.type.name}"
    
    
class TransactionDetail(models.Model):
    transaction = models.ForeignKey(
        Transaction, 
        on_delete=models.CASCADE,
        related_name='details'
    )
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.PROTECT,
        related_name='transaction_details'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = (('transaction', 'bank_account'),)

    def __str__(self):
        return f"{self.transaction} - {self.bank_account} - {self.amount}"
    