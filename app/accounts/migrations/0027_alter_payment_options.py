# Generated by Django 4.1.3 on 2023-05-17 11:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_payment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payment',
            options={'verbose_name': 'پرداخت', 'verbose_name_plural': 'پرداخت ها'},
        ),
    ]
