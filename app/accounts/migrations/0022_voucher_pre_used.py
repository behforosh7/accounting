# Generated by Django 4.1.3 on 2022-12-12 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_alter_voucher_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='pre_used',
            field=models.BigIntegerField(default=0, help_text='به مگابایت', verbose_name='حجم مصرف شده قبلی'),
        ),
    ]
