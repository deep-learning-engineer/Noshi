# Generated by Django 5.1.7 on 2025-06-09 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduled_transfers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledtransfers',
            name='end_date',
            field=models.DateField(null=True),
        ),
    ]
