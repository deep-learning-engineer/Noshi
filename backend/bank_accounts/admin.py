from django.contrib import admin
from .models import BankAccount, UserBankAccount


admin.site.register(BankAccount)
admin.site.register(UserBankAccount)
