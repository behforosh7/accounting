# Generated by Django 4.1.6 on 2023-05-17 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0028_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='message',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='پیام'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='reference',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='شماره پیگیری'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='token',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='توکن پرداخت'),
        ),
    ]
