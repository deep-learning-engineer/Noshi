# Generated by Django 5.1.7 on 2025-06-05 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bank_accounts', '0011_alter_bankaccount_table_and_more'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='userbankaccount',
            table='user_bank_accounts',
        ),
    ]
