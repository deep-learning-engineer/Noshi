from django.db import models
from users.models import User


class BankAccount(models.Model):
    ACCOUNT_STATUS = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('closed', 'Closed'),
    ]
    
    bank_account_id = models.AutoField(primary_key=True)
    account_number = models.CharField(max_length=20, unique=True, editable=False)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ACCOUNT_STATUS, default='active')

    def __str__(self):
        return f"{self.account_number} - {self.balance}"
    
    def save(self, *args, **kwargs):
        if not self.account_number:
            last_account = BankAccount.objects.order_by('-account_number').first()
            last_number = int(last_account.account_number) if last_account else 0
            self.account_number = str(last_number + 1).zfill(20)
        
        super().save(*args, **kwargs)
        

class UserBankAccount(models.Model):
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.CASCADE,
        related_name='users'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )

    class Meta:
        unique_together = (('bank_account', 'user'),)

    def __str__(self):
        return f"{self.user} - {self.bank_account}"
