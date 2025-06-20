# Generated by Django 5.1.7 on 2025-06-14 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('savings_accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingsaccount',
            name='is_first_deposit',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='savingsaccount',
            name='min_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
