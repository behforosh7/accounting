# Generated by Django 4.1.6 on 2023-05-19 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0031_payment_activate_alter_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='reference',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='شماره پیگیری'),
        ),
    ]
