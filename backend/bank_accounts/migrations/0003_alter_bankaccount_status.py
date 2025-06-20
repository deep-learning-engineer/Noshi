# Generated by Django 5.1.7 on 2025-05-03 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank_accounts', '0002_alter_userbankaccount_bank_account_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('frozen', 'Frozen'), ('closed', 'Closed')], default='active', editable=False, max_length=10),
        ),
    ]
